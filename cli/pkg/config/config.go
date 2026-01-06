package config

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"github.com/user/windmill-cli/pkg/keyring"
	"github.com/user/windmill-cli/pkg/logger"
)

type Context struct {
	ServerURL   string `json:"server_url"`
	AccessToken string `json:"access_token,omitempty"` // omitempty to avoid saving empty string
	Email       string `json:"email"`
}

type Config struct {
	CurrentContext string             `json:"current_context"`
	Contexts       map[string]Context `json:"contexts"`
}

// LegacyConfig for backward compatibility migration
type LegacyConfig struct {
	ServerURL   string `json:"server_url"`
	AccessToken string `json:"access_token"`
	Email       string `json:"email"`
}

func GetConfigDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".contextworks")
}

func GetConfigPath() string {
	return filepath.Join(GetConfigDir(), "config.json")
}

func Load() (*Config, error) {
	path := GetConfigPath()
	data, err := ioutil.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return &Config{
				CurrentContext: "default",
				Contexts:       make(map[string]Context),
			}, nil
		}
		return nil, err
	}

	// Try to decode as new config
	var config Config
	if err := json.Unmarshal(data, &config); err == nil && config.Contexts != nil {
		// Populate tokens from keyring
		for name, ctx := range config.Contexts {
			token, err := keyring.Get(name)
			if err == nil && token != "" {
				ctx.AccessToken = token
                // Update the map value
				config.Contexts[name] = ctx
				logger.Debug(fmt.Sprintf("Loaded token for '%s' from keyring", name))
			}
		}
		return &config, nil
	}

	// Fallback/Migrate: Try legacy
	var legacy LegacyConfig
	if err := json.Unmarshal(data, &legacy); err == nil {
		// Migrate to new format
		newConfig := &Config{
			CurrentContext: "default",
			Contexts: map[string]Context{
				"default": {
					ServerURL:   legacy.ServerURL,
					AccessToken: legacy.AccessToken,
					Email:       legacy.Email,
				},
			},
		}
		// Try to save immediately to trigger keyring migration
		Save(newConfig)
		return newConfig, nil
	}

	return nil, fmt.Errorf("invalid config format")
}

func Save(config *Config) error {
	dir := GetConfigDir()
	if err := os.MkdirAll(dir, 0700); err != nil {
		return err
	}

	// Create a copy to modify for saving (don't want to mutate the in-memory config that has tokens)
	saveConfig := Config{
		CurrentContext: config.CurrentContext,
		Contexts:       make(map[string]Context),
	}

	for name, ctx := range config.Contexts {
		// Try to save token to keyring
		if ctx.AccessToken != "" {
			err := keyring.Set(name, ctx.AccessToken)
			if err == nil {
				logger.Debug(fmt.Sprintf("Saved token for '%s' to keyring", name))
				// Clear token from file struct
				ctx.AccessToken = "" 
			} else {
				logger.Warning(fmt.Sprintf("Failed to save token to keyring for '%s': %v. Falling back to file.", name, err))
				// Leave AccessToken in ctx, so it saves to file
			}
		}
		saveConfig.Contexts[name] = ctx
	}

	data, err := json.MarshalIndent(saveConfig, "", "  ")
	if err != nil {
		return err
	}

	return ioutil.WriteFile(GetConfigPath(), data, 0600)
}

func (c *Config) GetCurrent() *Context {
	if c.Contexts == nil {
		return nil
	}
	if ctx, ok := c.Contexts[c.CurrentContext]; ok {
		return &ctx
	}
	return nil
}

func (c *Config) SetCurrent(name string, ctx Context) {
	if c.Contexts == nil {
		c.Contexts = make(map[string]Context)
	}
	c.Contexts[name] = ctx
	c.CurrentContext = name
}
