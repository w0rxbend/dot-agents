/*
Channel-Based Pagination Example (Go)

Demonstrates using channels for concurrent iteration over paginated results.
*/

package main

import (
	"context"
	"fmt"
	"os"
)

type User struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

type ChannelPaginationClient struct {
	apiKey string
}

func NewChannelPaginationClient(apiKey string) *ChannelPaginationClient {
	return &ChannelPaginationClient{apiKey: apiKey}
}

// fetchPage stands in for a real API call: it returns one page of users and
// the cursor for the next page ("" when there are no more pages).
func (c *ChannelPaginationClient) fetchPage(ctx context.Context, cursor string, limit int) ([]User, string, error) {
	pages := map[string]struct {
		users []User
		next  string
	}{
		"":      {[]User{{ID: "1", Name: "Alice", Email: "alice@example.com"}, {ID: "2", Name: "Bob", Email: "bob@example.com"}}, "page2"},
		"page2": {[]User{{ID: "3", Name: "Carol", Email: "carol@example.com"}}, ""},
	}
	if err := ctx.Err(); err != nil {
		return nil, "", err
	}
	p, ok := pages[cursor]
	if !ok {
		return nil, "", fmt.Errorf("unknown cursor %q", cursor)
	}
	if limit > 0 && len(p.users) > limit {
		p.users = p.users[:limit]
	}
	return p.users, p.next, nil
}

// ListUsers returns channels for users and errors
func (c *ChannelPaginationClient) ListUsers(ctx context.Context, limit int) (<-chan User, <-chan error) {
	userCh := make(chan User)
	errCh := make(chan error, 1)

	go func() {
		defer close(userCh)
		defer close(errCh)

		cursor := ""
		for {
			users, next, err := c.fetchPage(ctx, cursor, limit)
			if err != nil {
				errCh <- err
				return
			}

			for _, user := range users {
				select {
				case <-ctx.Done():
					errCh <- ctx.Err()
					return
				case userCh <- user:
				}
			}

			if next == "" {
				return // no more pages
			}
			cursor = next
		}
	}()

	return userCh, errCh
}

func main() {
	client := NewChannelPaginationClient(os.Getenv("API_KEY"))
	ctx := context.Background()

	userCh, errCh := client.ListUsers(ctx, 100)

	for user := range userCh {
		fmt.Printf("- %s (%s)\n", user.Name, user.Email)
	}

	if err := <-errCh; err != nil {
		fmt.Printf("Error: %v\n", err)
	}
}
