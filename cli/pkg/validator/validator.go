package validator

import (
    "fmt"
    "strings"

    "gopkg.in/yaml.v3"
)

type ToolMetadata struct {
    Name        string      `yaml:"name"`
    Description string      `yaml:"description"`
}

// ValidateYAML checks if the YAML content has required fields
func ValidateYAML(content []byte) error {
    var meta ToolMetadata
    if err := yaml.Unmarshal(content, &meta); err != nil {
        return fmt.Errorf("invalid YAML syntax: %w", err)
    }

    if meta.Name == "" {
        return fmt.Errorf("missing 'name' field")
    }
    if meta.Description == "" {
        return fmt.Errorf("missing 'description' field")
    }
    return nil
}

// ValidateScript checks if the script content is valid (basic checks)
func ValidateScript(content []byte) error {
    s := string(content)
    if len(bytesTrimSpace(content)) == 0 {
        return fmt.Errorf("script is empty")
    }
    if !strings.Contains(s, "def main(") && !strings.Contains(s, "def handler(") {
        // Warning level maybe? Or required convention?
        // For now, let's just ensure it's not empty.
    }
    return nil
}

func bytesTrimSpace(b []byte) []byte {
    return []byte(strings.TrimSpace(string(b)))
}
