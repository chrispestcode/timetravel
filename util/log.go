package util

import "log"

// LogError logs err if it is non-nil.
func LogError(err error) {
	if err != nil {
		log.Printf("error: %v", err)
	}
}
