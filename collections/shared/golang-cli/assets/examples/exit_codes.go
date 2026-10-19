package main

import (
	"errors"
	"fmt"
	"os"

	"github.com/you/myapp/cmd"
)

// Pattern for mapping errors to exit codes.
func mainWithExitCodes() {
	if err := cmd.Execute(); err != nil {
		// SilenceErrors is set on the root command, so Cobra did not print the error.
		fmt.Fprintln(os.Stderr, "Error:", err)
		var exitErr *ExitError
		if errors.As(err, &exitErr) {
			os.Exit(exitErr.Code)
		}
		os.Exit(1)
	}
}

type ExitError struct {
	Code int
	Err  error
}

func (e *ExitError) Error() string { return e.Err.Error() }
func (e *ExitError) Unwrap() error { return e.Err }
