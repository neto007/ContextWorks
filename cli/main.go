package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/user/windmill-cli/pkg/config"
	"github.com/user/windmill-cli/pkg/logger"
)

var (
	version   = "1.0.0"
	jsonFlag  bool
	debugFlag bool
)

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

var rootCmd = &cobra.Command{
	Use:   "contextworks",
	Short: "ContextWorks CLI - Script synchronization tool",
	Long: `ContextWorks CLI is a tool to synchronize your local Python scripts
with the ContextWorks server. It automatically detects categories and tools
based on your directory structure and keeps your server in sync.`,
	Version: version,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		logger.JSONMode = jsonFlag
		logger.DebugMode = debugFlag
	},
}

func init() {
	rootCmd.PersistentFlags().BoolVar(&jsonFlag, "json", false, "Output in JSON format")
	rootCmd.PersistentFlags().BoolVar(&debugFlag, "debug", false, "Enable debug logging")

	rootCmd.AddCommand(syncCmd)
	rootCmd.AddCommand(pullCmd)
	rootCmd.AddCommand(loginCmd)
	rootCmd.AddCommand(logoutCmd)
	rootCmd.AddCommand(whoamiCmd)
	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(updateCmd)
}

var logoutCmd = &cobra.Command{
	Use:   "logout",
	Short: "Logout and remove saved credentials",
	Run: func(cmd *cobra.Command, args []string) {
		configPath := config.GetConfigPath()
		if err := os.Remove(configPath); err != nil {
			if !os.IsNotExist(err) {
				logger.Error("Failed to remove config", err)
				return
			}
		}
		logger.Success("Logged out successfully!")
	},
}

var whoamiCmd = &cobra.Command{
	Use:   "whoami",
	Short: "Show current logged in user",
	Run: func(cmd *cobra.Command, args []string) {
		conf, err := config.Load()
		if err != nil {
			logger.Error("Failed to load config", err)
			return
		}
		ctx := conf.GetCurrent()
		if ctx == nil {
			logger.Error("Not logged in. Run 'contextworks login' first.", nil)
			return
		}
		logger.Info(fmt.Sprintf("👤 Logged in as: %s", ctx.Email))
		logger.Info(fmt.Sprintf("🔗 Server: %s", ctx.ServerURL))
	},
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the version number of contextworks",
	Run: func(cmd *cobra.Command, args []string) {
		logger.Info(fmt.Sprintf("contextworks version %s", version))
	},
}
