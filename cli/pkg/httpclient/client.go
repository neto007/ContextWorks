package httpclient

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/user/windmill-cli/pkg/logger"
)

const (
	MaxRetries = 3
	BaseDelay  = 500 * time.Millisecond
)

type Client struct {
	BaseURL string
	Token   string
	HTTP    *http.Client
}

func New(baseURL, token string) *Client {
	return &Client{
		BaseURL: baseURL,
		Token:   token,
		HTTP:    &http.Client{Timeout: 30 * time.Second},
	}
}

func (c *Client) Request(method, path string, body []byte) (*http.Response, error) {
    return c.RequestWithHeaders(method, path, body, map[string]string{"Content-Type": "application/json"})
}

func (c *Client) RequestWithHeaders(method, path string, body []byte, headers map[string]string) (*http.Response, error) {
	url := fmt.Sprintf("%s%s", c.BaseURL, path)
	var req *http.Request
	var err error

	for i := 0; i <= MaxRetries; i++ {
		if body != nil {
			req, err = http.NewRequest(method, url, bytes.NewBuffer(body))
		} else {
			req, err = http.NewRequest(method, url, nil)
		}

		if err != nil {
			return nil, err
		}

        // Apply custom headers
        for k, v := range headers {
            req.Header.Set(k, v)
        }

		if c.Token != "" {
			req.Header.Set("Authorization", "Bearer "+c.Token)
		}

		resp, err := c.HTTP.Do(req)
		if err == nil && resp.StatusCode < 500 {
			// Success or non-retriable error (4xx)
			return resp, nil
		}

		// Close body if response exists to prevent leaks during retry
		if resp != nil {
			resp.Body.Close()
		}

		// Log and wait if retrying
		if i < MaxRetries {
			delay := BaseDelay * time.Duration(1<<i) // Exponential backoff
			errMsg := "network error"
			if err != nil {
				errMsg = err.Error()
			} else {
				errMsg = fmt.Sprintf("status code %d", resp.StatusCode)
			}
			
			logger.Debug(fmt.Sprintf("Request failed (%s). Retrying in %v...", errMsg, delay))
			time.Sleep(delay)
		} else {
            // Return last error
            if err != nil {
                return nil, err
            }
            return nil, fmt.Errorf("server error (status %d) after %d retries", resp.StatusCode, MaxRetries)
        }
	}
	return nil, fmt.Errorf("request failed after retries")
}

func (c *Client) ReadBody(resp *http.Response) ([]byte, error) {
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}
