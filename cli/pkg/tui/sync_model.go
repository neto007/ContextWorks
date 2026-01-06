package tui

import (
	"fmt"

	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type ValidationMsg struct {
    Err error
}

type SyncMsg struct {
    Message string
    Done    bool
    Err     error
}

type SyncModel struct {
	spinner   spinner.Model
	status    string
    details   string
	err       error
	done      bool
    quitting  bool
}

func NewSyncModel() SyncModel {
	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("205"))

	return SyncModel{
		spinner: s,
		status:  "Initializing sync...",
	}
}

func (m SyncModel) Init() tea.Cmd {
	return m.spinner.Tick
}

func (m SyncModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
        if msg.String() == "q" || msg.String() == "ctrl+c" {
			m.quitting = true
			return m, tea.Quit
		}
		return m, nil

    case SyncMsg:
        if msg.Err != nil {
            m.err = msg.Err
            m.status = "Sync failed!"
            m.done = true
            return m, tea.Quit
        }
        if msg.Done {
            m.done = true
            m.status = msg.Message
            return m, tea.Quit
        }
        m.status = msg.Message
        return m, nil

	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spinner, cmd = m.spinner.Update(msg)
		return m, cmd

	default:
		return m, nil
	}
}

func (m SyncModel) View() string {
	if m.err != nil {
		return fmt.Sprintf("\n❌ Error: %v\n", m.err)
	}
    if m.done {
        return fmt.Sprintf("\n✅ %s\n", m.status)
    }
	if m.quitting {
		return "\n🚫 Sync Cancelled\n"
	}

	str := fmt.Sprintf("\n %s %s\n", m.spinner.View(), m.status)
    if m.details != "" {
        str += fmt.Sprintf("   %s\n", lipgloss.NewStyle().Foreground(lipgloss.Color("240")).Render(m.details))
    }
	return str
}
