// cmd/myapp/main.go
package main

import (
	"fmt"
	"os"
)

func main() {
	if err := Execute(); err != nil {
		// rootCmd sets SilenceErrors, so Cobra does not print the error: do it here.
		fmt.Fprintln(os.Stderr, "Error:", err)
		os.Exit(1)
	}
}
