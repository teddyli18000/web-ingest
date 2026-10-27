package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestDriveHTTPFinalResponseRequiresVerificationMetadata(t *testing.T) {
	cases := []struct {
		name string
		body string
	}{
		{"empty", ``},
		{"missing id", `{"size":"17","md5Checksum":"0123456789abcdef0123456789abcdef"}`},
		{"missing size", `{"id":"abc","md5Checksum":"0123456789abcdef0123456789abcdef"}`},
		{"missing md5", `{"id":"abc","size":"17"}`},
		{"invalid md5", `{"id":"abc","size":"17","md5Checksum":"not-a-digest"}`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				fmt.Fprint(w, tc.body)
			}))
			defer server.Close()
			client := &driveResumableHTTP{Client: server.Client()}
			_, err := client.Upload(context.Background(), server.URL, 0, 16, 17, strings.NewReader("0123456789abcdefg"))
			if err == nil {
				t.Fatal("expected strict final metadata error")
			}
		})
	}
}
