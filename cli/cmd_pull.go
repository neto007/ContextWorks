package main

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/user/windmill-cli/pkg/config"
	"github.com/user/windmill-cli/pkg/logger"
)

var (
	pullDir string
)

var pullCmd = &cobra.Command{
	Use:   "pull",
	Short: "Download scripts from the server to local filesystem",
	Long: `Pull fetches all workspaces and tools from the ContextWorks server and 
recreates the directory structure and .py files locally. 

This is useful for recreating your local 'f' folder from the database or
setting up a new development environment.`,
	Example: `  # Pull scripts to current directory
  contextworks pull

  # Pull to a specific directory
  contextworks pull --dir ./f_new

  # Pull using specific server
  contextworks pull --url http://127.0.0.1:8001`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// Load config if needed
		if authToken == "" || serverURL == "http://localhost:8001" {
			conf, err := config.Load()
			if err == nil && conf != nil {
				ctx := conf.GetCurrent()
				if ctx != nil {
					if authToken == "" {
						authToken = ctx.AccessToken
					}
					if serverURL == "http://localhost:8001" {
						serverURL = ctx.ServerURL
					}
					logger.Info(fmt.Sprintf("🔐 Using saved credentials (logged in as %s)", ctx.Email))
				}
			}
		}

		logger.Info(fmt.Sprintf("📥 Pulling scripts from '%s' to '%s'...", serverURL, pullDir))
		
		if err := pullScripts(pullDir, serverURL, authToken); err != nil {
			return fmt.Errorf("pull failed: %w", err)
		}
		
		logger.Success("✅ Pull completed successfully!")
		return nil
	},
}

func init() {
	pullCmd.Flags().StringVarP(&pullDir, "dir", "d", ".", "Directory to pull scripts into")
	pullCmd.Flags().StringVarP(&serverURL, "url", "u", "http://localhost:8001", "Base URL of the server")
	pullCmd.Flags().StringVarP(&authToken, "token", "t", "", "Authentication token (optional)")
}
