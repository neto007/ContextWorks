package main

import (
	"fmt"

	"github.com/spf13/cobra"
    tea "github.com/charmbracelet/bubbletea"
	"github.com/user/windmill-cli/pkg/config"
	"github.com/user/windmill-cli/pkg/logger"
    "github.com/user/windmill-cli/pkg/tui"
)

var (
	syncDir   string
	serverURL string
	authToken string
	pruneFlag bool
    buildFlag bool
)

var syncCmd = &cobra.Command{
	Use:   "sync",
	Short: "Synchronize local scripts with the server",
	Long: `Sync walks through the specified directory and synchronizes all Python scripts
with the ContextWorks server. It creates new tools if they don't exist and updates
existing ones.

The directory structure should be:
  category1/
    tool1.py
    tool2.py
  category2/
    tool3.py
    
Where each folder represents a category and each .py file is a tool.`,
	Example: `  # Sync current directory
  contextworks sync

  # Sync specific directory
  contextworks sync --dir /path/to/scripts

  # Sync and remove remote tools missing locally
  contextworks sync

  # Sync with custom server URL
  contextworks sync --dir ./f --url http://localhost:8000

  # Sync with authentication
  contextworks sync --token your_auth_token`,
	RunE: func(cmd *cobra.Command, args []string) error {
		// If no token provided, try to load from config
		if authToken == "" {
			conf, err := config.Load()
			if err != nil {
				return fmt.Errorf("failed to load config: %w", err)
			}
			if conf != nil {
				ctx := conf.GetCurrent()
				if ctx != nil {
					authToken = ctx.AccessToken
					if serverURL == "http://localhost:8001" {
						serverURL = ctx.ServerURL
					}
					// Only log this if NOT in JSON mode to avoid polluting output, or use Debug
                    if !logger.JSONMode {
					    logger.Info(fmt.Sprintf("🔐 Using saved credentials (logged in as %s)", ctx.Email))
                    }
				}
			}
		}
		
        if logger.JSONMode {
            // Non-interactive mode
            if err := syncScripts(syncDir, serverURL, authToken, pruneFlag, buildFlag, nil); err != nil {
                return fmt.Errorf("sync failed: %w", err)
            }
            logger.Success("Sync completed successfully")
            return nil
        }
        
        // Interactive TUI Mode
        updates := make(chan tui.SyncMsg)
        model := tui.NewSyncModel()
        p := tea.NewProgram(model)

        // Run sync in goroutine
        go func() {
            if err := syncScripts(syncDir, serverURL, authToken, pruneFlag, buildFlag, updates); err != nil {
                updates <- tui.SyncMsg{Err: err}
            } else {
                // Done is handled by syncScripts summary, but safety close
                // syncScripts closes channel when done
            }
        }()

        // Run TUI listener in goroutine to update program
        go func() {
            for msg := range updates {
                p.Send(msg)
            }
        }()

        if _, err := p.Run(); err != nil {
            return fmt.Errorf("tui failed: %w", err)
        }
		
		return nil
	},
}

func init() {
	syncCmd.Flags().StringVarP(&syncDir, "dir", "d", ".", "Directory to sync scripts from")
	syncCmd.Flags().StringVarP(&serverURL, "url", "u", "http://localhost:8001", "Base URL of the server")
	syncCmd.Flags().StringVarP(&authToken, "token", "t", "", "Authentication token (optional)")
	syncCmd.Flags().BoolVarP(&pruneFlag, "prune", "p", false, "Delete tools on server that are missing locally")
    syncCmd.Flags().BoolVarP(&buildFlag, "build", "b", false, "Trigger build for new/updated tools")
}
