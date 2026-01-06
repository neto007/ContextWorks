package logger

import (
	"encoding/json"
	"os"

	"github.com/pterm/pterm"
)

var (
	JSONMode  bool
	DebugMode bool
)

type LogMessage struct {
	Level   string `json:"level"`
	Message string `json:"message"`
	Detail  string `json:"detail,omitempty"`
}

func Info(msg string) {
	if JSONMode {
		logJSON("info", msg, "")
		return
	}
	pterm.Info.Println(msg)
}

func Success(msg string) {
	if JSONMode {
		logJSON("success", msg, "")
		return
	}
	pterm.Success.Println(msg)
}

func Error(msg string, err error) {
	if JSONMode {
		detail := ""
		if err != nil {
			detail = err.Error()
		}
		logJSON("error", msg, detail)
		return
	}
	pterm.Error.Println(msg)
	if err != nil && DebugMode {
		pterm.Debug.Println(err.Error())
	}
}

func Warning(msg string) {
	if JSONMode {
		logJSON("warning", msg, "")
		return
	}
	pterm.Warning.Println(msg)
}

func Debug(msg string) {
	if !DebugMode {
		return
	}
	if JSONMode {
		logJSON("debug", msg, "")
		return
	}
	pterm.Debug.Println(msg)
}

func logJSON(level, msg, detail string) {
	log := LogMessage{
		Level:   level,
		Message: msg,
		Detail:  detail,
	}
	encoder := json.NewEncoder(os.Stdout)
	encoder.Encode(log)
}
