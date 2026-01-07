package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
	"regexp"

	"github.com/user/windmill-cli/pkg/httpclient"
	"github.com/user/windmill-cli/pkg/logger"
    "github.com/user/windmill-cli/pkg/tui"
	"github.com/user/windmill-cli/pkg/validator"
)

// sanitizeName normalizes a name to lowercase and removes special characters
func sanitizeName(name string) string {
	// Convert to lowercase - REMOVED to preserve case compatibility with existing DB
	// name = strings.ToLower(name)
	// Replace non-alphanumeric characters with dash
	reg := regexp.MustCompile(`[^\w\-]+`)
	name = reg.ReplaceAllString(name, "-")
	// Remove multiple dashes
	reg = regexp.MustCompile(`-+`)
	name = reg.ReplaceAllString(name, "-")
	// Remove leading/trailing dashes
	name = strings.Trim(name, "-")
	return name
}

type ToolArgument struct {
	Name        string      `json:"name" yaml:"name"`
	Type        string      `json:"type" yaml:"type"`
	Description string      `json:"description" yaml:"description"`
	Default     interface{} `json:"default,omitempty" yaml:"default,omitempty"`
	Required    bool        `json:"required" yaml:"required"`
}

type YAMLMetadata struct {
	Name        string         `yaml:"name"`
	Description string         `yaml:"description"`
	Arguments   []ToolArgument `yaml:"arguments"`
}

type ToolRequest struct {
	Name         string         `json:"name"`
	Description  string         `json:"description,omitempty"`
	ScriptCode   string         `json:"script_code"`
	Arguments    []ToolArgument `json:"arguments,omitempty"`
	Requirements string         `json:"requirements,omitempty"`
}

func syncScripts(baseDir string, baseURL string, token string, prune bool, build bool, updates chan<- tui.SyncMsg) error {
    if updates != nil {
        defer close(updates)
    }

    sendUpdate := func(msg string) {
        if updates != nil {
            updates <- tui.SyncMsg{Message: msg}
        } else {
            logger.Info(msg)
        }
    }
    

	scriptsProcessed := 0
	scriptsUpdated := 0
	scriptsFailed := 0
    scriptsDeleted := 0

    // Ensure base directory exists
    if _, err := os.Stat(baseDir); os.IsNotExist(err) {
        return fmt.Errorf("directory '%s' does not exist", baseDir)
    }

    // 0. FETCH KNOWN CATEGORIES
    knownCategories := make(map[string]bool)
    
    // Fetch existing workspaces
    // Fetch existing workspaces
    client := httpclient.New(baseURL, token)
    resp, err := client.Request("GET", "/api/workspaces", nil)
    if err == nil && resp.StatusCode == 200 {
        var workspaces []struct {
            Name string `json:"name"`
        }
        if err := json.NewDecoder(resp.Body).Decode(&workspaces); err == nil {
            for _, ws := range workspaces {
                knownCategories[ws.Name] = true
            }
        }
        resp.Body.Close()
    } else {
        logger.Warning("Could not fetch existing workspaces. Auto-creation might fail.")
    }

    // Helper to create category
    ensureCategory := func(name string) {
        if knownCategories[name] {
            return
        }
        
        sendUpdate(fmt.Sprintf("✨ Creating workspace '%s'...", name))
        
        type CreateWSReq struct {
            Name        string `json:"name"`
            Description string `json:"description"`
        }
        
        reqBody, _ := json.Marshal(CreateWSReq{
            Name:        name,
            Description: "Auto-created by CLI",
        })
        
        resp, err := client.Request("POST", "/api/workspaces", reqBody)
        if err != nil {
            if updates == nil { logger.Error("Failed to create workspace", err) }
            return
        }
        defer resp.Body.Close()
        
        if resp.StatusCode == 200 || resp.StatusCode == 201 || resp.StatusCode == 400 {
            // 400 might mean it exists, which is fine
            knownCategories[name] = true
            if updates == nil { logger.Success("Done") }
        } else {
            if updates == nil { logger.Error("Failed", fmt.Errorf("status %d", resp.StatusCode)) }
        }
    }

    // Track tools that need building
    type ToolID struct {
        Category string
        Name     string
    }
    var toolsToBuild []ToolID

    // 1. SYNC UPSTREAM (Add/Update)
	err = filepath.Walk(baseDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			if strings.HasPrefix(info.Name(), ".") || 
			   info.Name() == "__pycache__" || 
			   info.Name() == "node_modules" ||
			   info.Name() == "venv" {
				return filepath.SkipDir
			}
			return nil
		}

		// Process .py and .yaml files
        ext := filepath.Ext(path)
		if (ext == ".py" && info.Name() != "__init__.py") || ext == ".yaml" {
			relPath, _ := filepath.Rel(baseDir, path)
			parts := strings.Split(relPath, string(os.PathSeparator))

			if len(parts) >= 2 {
                // Check/Create Category
                categoryName := parts[0]
                ensureCategory(categoryName)

                // normalizedRelPath structure: Category/Tool.py
                normalizedRelPath := filepath.ToSlash(relPath)
                
                sendUpdate(fmt.Sprintf("📤 Syncing %s...", normalizedRelPath))
                
                content, err := ioutil.ReadFile(path)
                if err != nil {
					logger.Error("Failed to read", err)
					scriptsFailed++
					return nil
				}

                // Pre-flight Validation
                if ext == ".yaml" {
                    if err := validator.ValidateYAML(content); err != nil {
                        logger.Error("Validation failed", fmt.Errorf("%s: %w", normalizedRelPath, err))
                        scriptsFailed++
                        return nil
                    }
                } else if ext == ".py" {
                    if err := validator.ValidateScript(content); err != nil {
                        logger.Error("Validation failed", fmt.Errorf("%s: %w", normalizedRelPath, err))
                        scriptsFailed++
                        return nil
                    }
                }
                
                type ToolContentRequest struct {
                    Path    string `json:"path"`
                    Content string `json:"content"`
                }
                
                reqBody := ToolContentRequest{
                    Path:    normalizedRelPath,
                    Content: string(content),
                }

				jsonBody, _ := json.Marshal(reqBody)

				resp, reqErr := client.Request("POST", "/api/tools/content", jsonBody)
				if reqErr != nil {
					logger.Error("Request failed", reqErr)
					scriptsFailed++
					return nil
				}
				defer resp.Body.Close()
                
                if resp.StatusCode >= 200 && resp.StatusCode < 300 {
                    var contentResp struct {
                        Status  string `json:"status"`
                        Changed bool   `json:"changed"`
                    }
                    isChanged := true // Default for backward compatibility
                    if err := json.NewDecoder(resp.Body).Decode(&contentResp); err == nil {
                        isChanged = contentResp.Changed
                    }
                    
                    if updates == nil { 
                        if isChanged {
                            logger.Success("Done (Updated)")
                        } else {
                            logger.Info("Done (No changes)")
                        }
                    }
					scriptsUpdated++
                    
                    // Track for build ONLY IF content or config changed
                    if isChanged {
                        // The Name is parts[1] without extension.
                        toolShortName := strings.TrimSuffix(parts[1], ext)
                        
                        // Avoid adding duplicate if we visit both .py and .yaml
                        found := false
                        for _, t := range toolsToBuild {
                            if t.Category == categoryName && t.Name == toolShortName {
                                found = true
                                break
                            }
                        }
                        if !found {
                            toolsToBuild = append(toolsToBuild, ToolID{Category: categoryName, Name: toolShortName})
                        }
                    }

				} else {
					bodyBytes, _ := ioutil.ReadAll(resp.Body)
					logger.Error(fmt.Sprintf("Failed (%d)", resp.StatusCode), fmt.Errorf("%s", string(bodyBytes)))
					scriptsFailed++
				}
                
                scriptsProcessed++
            }
        }
        return nil
    })
    
    if err != nil {
		return err
	}

    // 2. PRUNE (Delete remote tools missing locally)
    if prune {
        sendUpdate("Pruning remote tools...")
        // Reuse client
        resp, err := client.Request("GET", "/api/tools", nil)
        if err != nil {
            logger.Error("Failed to fetch remote tools for pruning", err)
        } else {
            defer resp.Body.Close()
            
            if resp.StatusCode != 200 {
                logger.Error("Failed to fetch remote tools list", fmt.Errorf("status %d", resp.StatusCode))
            } else {
                var categories map[string][]struct {
                    ID       string `json:"id"`
                }
                if err := json.NewDecoder(resp.Body).Decode(&categories); err != nil {
                     logger.Error("Failed to parse remote tools list", err)
                } else {
                    for catName, tools := range categories {
                        catDir := filepath.Join(baseDir, catName)
                        
                        for _, tool := range tools {
                            shortID := tool.ID
                            if strings.Contains(tool.ID, "/") {
                                parts := strings.Split(tool.ID, "/")
                                shortID = parts[len(parts)-1]
                            }
                            
                            pyPath := filepath.Join(catDir, shortID+".py")
                            yamlPath := filepath.Join(catDir, shortID+".yaml")
                            
                            _, errPy := os.Stat(pyPath)
                            _, errYaml := os.Stat(yamlPath)
                            
                            existsLocally := !os.IsNotExist(errPy) || !os.IsNotExist(errYaml)
                            
                            if !existsLocally {
                                sendUpdate(fmt.Sprintf("🗑️  Deleting %s/%s...", catName, shortID))
                                
                                path := fmt.Sprintf("/api/tools/%s/%s", catName, shortID)
                                dResp, err := client.Request("DELETE", path, nil)
                                if err != nil {
                                     logger.Error("Request failed", err)
                                } else {
                                     defer dResp.Body.Close()
                                     if dResp.StatusCode >= 200 && dResp.StatusCode < 300 {
                                         logger.Success("Deleted")
                                         scriptsDeleted++
                                     } else {
                                         logger.Error("Failed", fmt.Errorf("status %d", dResp.StatusCode))
                                     }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // 3. BUILD
    if build && len(toolsToBuild) > 0 {
        sendUpdate("Triggering builds...")
        for _, t := range toolsToBuild {
             sendUpdate(fmt.Sprintf("🚀 Building %s/%s...", t.Category, t.Name))
             
             path := fmt.Sprintf("/api/tools/%s/%s/build", t.Category, t.Name)
             resp, err := client.Request("POST", path, nil)
             if err != nil {
                 logger.Error("Request failed", err)
             } else {
                 defer resp.Body.Close()
                 if resp.StatusCode >= 200 && resp.StatusCode < 300 {
                     var buildResp struct {
                         JobID string `json:"job_id"`
                     }
                     if err := json.NewDecoder(resp.Body).Decode(&buildResp); err == nil {
                        logger.Success(fmt.Sprintf("Started (Job: %s)", buildResp.JobID))
                     } else {
                        logger.Success("Started")
                     }
                 } else {
                     body, _ := ioutil.ReadAll(resp.Body)
                     logger.Warning(fmt.Sprintf("Skipped/Failed (%d): %s", resp.StatusCode, string(body)))
                 }
             }
        }
    }

	// Summary
    summary := fmt.Sprintf("Synced: %d, Failed: %d", scriptsUpdated, scriptsFailed)
    if prune {
        summary += fmt.Sprintf(", Deleted: %d", scriptsDeleted)
    }
    
    if updates != nil {
        updates <- tui.SyncMsg{Message: summary, Done: true}
    } else {
    	logger.Info("Summary:")
    	logger.Info(fmt.Sprintf("Total processed: %d", scriptsProcessed))
    	logger.Success(fmt.Sprintf("Synced: %d", scriptsUpdated))
        if prune {
            logger.Info(fmt.Sprintf("Deleted: %d", scriptsDeleted))
        }
    	if scriptsFailed > 0 {
    		logger.Error(fmt.Sprintf("Failed: %d", scriptsFailed), nil)
    	}
    }

	return nil
}

func uploadToolLogo(baseURL string, category string, toolID string, svgContent string, token string) error {
	client := httpclient.New(baseURL, token)
	path := fmt.Sprintf("/api/tools/%s/%s/logo", category, toolID)
	reqBody := map[string]string{"svg_code": svgContent}
	jsonBody, _ := json.Marshal(reqBody)

    // Note: Request handles content-type json automatically for body
    resp, err := client.Request("POST", path, jsonBody)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := ioutil.ReadAll(resp.Body)
		return fmt.Errorf("logo upload failed (%d): %s", resp.StatusCode, string(body))
	}
	return nil
}

func pullScripts(baseDir string, baseURL string, token string) error {
	logger.Info(fmt.Sprintf("Preparing to pull scripts into '%s'...", baseDir))

	// 1. Fetch all tools
	client := httpclient.New(baseURL, token)
	
    resp, err := client.Request("GET", "/api/tools", nil)
	if err != nil {
		return fmt.Errorf("failed to fetch tools: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		body, _ := ioutil.ReadAll(resp.Body)
		return fmt.Errorf("failed to fetch tools (%d): %s", resp.StatusCode, string(body))
	}

	var categories map[string][]struct {
		ID       string `json:"id"`
		Name     string `json:"name"`
		Category string `json:"category"`
		HasLogo  bool   `json:"has_logo"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&categories); err != nil {
		return fmt.Errorf("failed to decode tools list: %w", err)
	}

	totalPulled := 0
	
	// 2. Iterate through categories and tools
	for catName, tools := range categories {
		catDir := filepath.Join(baseDir, catName)
		if err := os.MkdirAll(catDir, 0755); err != nil {
			logger.Error(fmt.Sprintf("Failed to create directory %s", catDir), err)
			continue
		}

		logger.Info(fmt.Sprintf("Workspace: %s", catName))

		for _, tool := range tools {
			logger.Info(fmt.Sprintf("Pulling %s...", tool.ID))

			// Extract short ID (remove category prefix if present)
			shortID := tool.ID
			if strings.Contains(tool.ID, "/") {
				parts := strings.Split(tool.ID, "/")
				shortID = parts[len(parts)-1]
			}

			// Fetch tool details for script code
			path := fmt.Sprintf("/api/tools/%s/%s", catName, shortID)
            dResp, err := client.Request("GET", path, nil)

			if err != nil {
				logger.Error("Detail request failed", nil)
				continue
			}
			defer dResp.Body.Close()

			if dResp.StatusCode != 200 {
				logger.Error("Failed", fmt.Errorf("status %d", dResp.StatusCode))
				continue
			}

			var detail struct {
				ScriptCode string `json:"script_code"`
			}
			if err := json.NewDecoder(dResp.Body).Decode(&detail); err != nil {
				logger.Error("Decode failed", nil)
				continue
			}

			// Write script
			scriptPath := filepath.Join(catDir, shortID+".py")
			if err := ioutil.WriteFile(scriptPath, []byte(detail.ScriptCode), 0755); err != nil {
				logger.Error("Failed to write file", err)
				continue
			}

            // Fetch and write YAML
            yamlPath := fmt.Sprintf("/api/tools/content?tool_id=%s/%s&file_type=yaml", catName, shortID)
            yResp, err := client.Request("GET", yamlPath, nil)
            
            if err == nil && yResp.StatusCode == 200 {
                var yDetail struct {
                    Content string `json:"content"`
                }
                if err := json.NewDecoder(yResp.Body).Decode(&yDetail); err == nil {
                    yamlPath := filepath.Join(catDir, shortID+".yaml")
                    ioutil.WriteFile(yamlPath, []byte(yDetail.Content), 0644)
                }
                yResp.Body.Close()
            }

			// Pull logo if exists
			if tool.HasLogo {
				logoPath := fmt.Sprintf("/api/tools/%s/%s/logo", catName, tool.ID)
				lResp, err := client.Request("GET", logoPath, nil)

				if err == nil && lResp.StatusCode == 200 {
					logoContent, _ := ioutil.ReadAll(lResp.Body)
					logoPath := filepath.Join(catDir, shortID+".logo.svg")
					ioutil.WriteFile(logoPath, logoContent, 0644)
					lResp.Body.Close()
				}
			}

			logger.Success("Done")
			totalPulled++
		}
	}

	logger.Success(fmt.Sprintf("Successfully pulled %d scripts into '%s'!", totalPulled, baseDir))
	return nil
}
