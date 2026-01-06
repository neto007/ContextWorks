package keyring

import (
	"fmt"

	"github.com/user/windmill-cli/pkg/logger"
	"github.com/zalando/go-keyring"
)

const ServiceName = "ContextWorks"

// Set saves a token for a specific user (context)
func Set(user, token string) error {
	err := keyring.Set(ServiceName, user, token)
	if err != nil {
		logger.Debug(fmt.Sprintf("Keyring set failed: %v", err))
		return err
	}
	return nil
}

// Get retrieves a token for a specific user (context)
func Get(user string) (string, error) {
	token, err := keyring.Get(ServiceName, user)
	if err != nil {
		if err == keyring.ErrNotFound {
			return "", nil
		}
		logger.Debug(fmt.Sprintf("Keyring get failed: %v", err))
		return "", err
	}
	return token, nil
}

// Delete removes a token for a specific user (context)
func Delete(user string) error {
	err := keyring.Delete(ServiceName, user)
	if err != nil && err != keyring.ErrNotFound {
		logger.Debug(fmt.Sprintf("Keyring delete failed: %v", err))
		return err
	}
	return nil
}
