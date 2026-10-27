package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestStartSessionSendsMinimalMetadataAndUploadHints(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Fatalf("method=%s", r.Method)
		}
		if r.Header.Get("Authorization") != "Bearer token" {
			t.Fatalf("authorization=%q", r.Header.Get("Authorization"))
		}
		if r.Header.Get("X-Upload-Content-Type") != "application/octet-stream" || r.Header.Get("X-Upload-Content-Length") != "12345" {
			t.Fatalf("upload hints type=%q length=%q", r.Header.Get("X-Upload-Content-Type"), r.Header.Get("X-Upload-Content-Length"))
		}
		var metadata driveSessionMetadata
		if err := json.NewDecoder(r.Body).Decode(&metadata); err != nil {
			t.Fatal(err)
		}
		if metadata.Name != "file.bin" || len(metadata.Parents) != 1 || metadata.Parents[0] != "parent-id" {
			t.Fatalf("metadata=%+v", metadata)
		}
		w.Header().Set("Location", serverURL(r)+"session/opaque")
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	client := &driveResumableHTTP{
		Client:         server.Client(),
		AccessToken:    "token",
		UploadEndpoint: server.URL + "/upload?uploadType=resumable",
	}
	location, err := client.StartSession(context.Background(), "file.bin", "parent-id", 12345)
	if err != nil {
		t.Fatal(err)
	}
	if location != server.URL+"/session/opaque" {
		t.Fatalf("location=%q", location)
	}
}

func TestStartSessionRequiresAuthBeforeNetwork(t *testing.T) {
	client := &driveResumableHTTP{}
	_, err := client.StartSession(context.Background(), "file.bin", "parent-id", 12345)
	if err == nil || err != errDriveAuthRequired {
		t.Fatalf("expected auth required, got %v", err)
	}
}

func TestStartSessionRejectsUnsafeFilename(t *testing.T) {
	client := &driveResumableHTTP{AccessToken: "token"}
	for _, name := range []string{"", "a/b", "bad\x00name"} {
		if _, err := client.StartSession(context.Background(), name, "parent", 1); err == nil {
			t.Fatalf("expected invalid filename %q", name)
		}
	}
}

func serverURL(r *http.Request) string {
	return fmt.Sprintf("http://%s/", r.Host)
}
