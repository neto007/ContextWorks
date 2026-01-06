package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"syscall"

	"github.com/spf13/cobra"
	"github.com/user/windmill-cli/pkg/config"
	"github.com/user/windmill-cli/pkg/httpclient"
	"github.com/user/windmill-cli/pkg/logger"
	"golang.org/x/term"
)

type LoginRequest struct {
	Email    string `json:"username"`
	Password string `json:"password"`
}

type LoginResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
}

var contextName string

var loginCmd = &cobra.Command{
	Use:   "login",
	Short: "Login to the ContextWorks server and save credentials",
	Long: `Login authenticates with the ContextWorks server using your email and password.
The access token is saved locally in ~/.contextworks/config.json.
You can use --context to save credentials to a specific profile (e.g. 'prod', 'dev').`,
	Example: `  # Login with default context
  contextworks login

  # Login to verify production server
  contextworks login --url https://api.contextworks.com --context prod`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Get email
		fmt.Print("📧 Email: ")
		var email string
		fmt.Scanln(&email)

		// Get password (hidden)
		fmt.Print("🔒 Password: ")
		passwordBytes, err := term.ReadPassword(int(syscall.Stdin))
		fmt.Println() // New line after password input
		if err != nil {
			return fmt.Errorf("failed to read password: %w", err)
		}
		password := string(passwordBytes)

		// Login
		logger.Info(fmt.Sprintf("🔄 Logging in to %s...", serverURL))
		
		// Prepare JSON body
		reqBody := LoginRequest{
			Email:    email,
			Password: password,
		}
		jsonBody, _ := json.Marshal(reqBody)
		
		client := httpclient.New(serverURL, "")
		resp, err := client.Request("POST", "/auth/login", jsonBody)
		if err != nil {
			return fmt.Errorf("login request failed: %w", err)
		}
		defer resp.Body.Close()
		
		if resp.StatusCode != 200 {
			bodyBytes, _ := ioutil.ReadAll(resp.Body)
			return fmt.Errorf("login failed (%d): %s", resp.StatusCode, string(bodyBytes))
		}
		
		var loginResp LoginResponse
		if err := json.NewDecoder(resp.Body).Decode(&loginResp); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}
		
		// Load existing config or create new
		conf, err := config.Load()
		if err != nil {
			// If error is other than not exist (which Load handles by returning empty), log it
			logger.Warning(fmt.Sprintf("Could not load existing config: %v. Creating new.", err))
			conf = &config.Config{}
		}
		
		// Save to context
		ctxName := "default"
		if contextName != "" {
			ctxName = contextName
		}
		
		conf.SetCurrent(ctxName, config.Context{
			ServerURL:   serverURL,
			AccessToken: loginResp.AccessToken,
			Email:       email,
		})
		
		if err := config.Save(conf); err != nil {
			return fmt.Errorf("failed to save config: %w", err)
		}
		
		logger.Success("✅ Login successful!")
		logger.Info(fmt.Sprintf("📝 Token saved to %s (Context: %s)", config.GetConfigPath(), ctxName))
		logger.Info(fmt.Sprintf("👤 Logged in as: %s", email))
		
		return nil
	},
}

func init() {
	loginCmd.Flags().StringVarP(&serverURL, "url", "u", "http://localhost:8001", "Base URL of the server")
	loginCmd.Flags().StringVarP(&contextName, "context", "c", "", "Context name (profile) to save credentials to")
}
