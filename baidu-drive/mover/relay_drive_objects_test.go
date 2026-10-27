package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

func TestCreateOrAdoptEmptyCreatesOnce(t *testing.T) {
	var created atomic.Bool
	var posts atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer token" {
			t.Fatalf("authorization=%q", r.Header.Get("Authorization"))
		}
		switch r.Method {
		case http.MethodGet:
			if !strings.Contains(r.URL.Query().Get("q"), "name = 'empty.bin'") {
				t.Fatalf("q=%q", r.URL.Query().Get("q"))
			}
			files := []driveListedFile{}
			if created.Load() {
				files = append(files, driveListedFile{ID: "file-1", Name: "empty.bin", Size: "0", MD5Checksum: emptyBlobMD5, MimeType: "application/octet-stream"})
			}
			_ = json.NewEncoder(w).Encode(driveFileList{Files: files})
		case http.MethodPost:
			posts.Add(1)
			var metadata driveCreateMetadata
			if err := json.NewDecoder(r.Body).Decode(&metadata); err != nil {
				t.Fatal(err)
			}
			if metadata.Name != "empty.bin" || len(metadata.Parents) != 1 || metadata.Parents[0] != "parent-1" {
				t.Fatalf("metadata=%+v", metadata)
			}
			created.Store(true)
			w.WriteHeader(http.StatusCreated)
			fmt.Fprintf(w, `{"id":"file-1","size":"0","md5Checksum":"%s"}`, emptyBlobMD5)
		default:
			t.Fatalf("method=%s", r.Method)
		}
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client(), AccessToken: "token", UploadEndpoint: server.URL + "/upload?uploadType=resumable"}
	first, err := client.CreateOrAdoptEmpty(context.Background(), "empty.bin", "parent-1")
	if err != nil {
		t.Fatal(err)
	}
	second, err := client.CreateOrAdoptEmpty(context.Background(), "empty.bin", "parent-1")
	if err != nil {
		t.Fatal(err)
	}
	if first.FileID != "file-1" || second.FileID != "file-1" || first.MD5Checksum != emptyBlobMD5 {
		t.Fatalf("first=%+v second=%+v", first, second)
	}
	if posts.Load() != 1 {
		t.Fatalf("posts=%d", posts.Load())
	}
}

func TestCreateOrAdoptEmptyReconcilesLostCreateResponse(t *testing.T) {
	var listed atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			if listed.Add(1) == 1 {
				_ = json.NewEncoder(w).Encode(driveFileList{Files: nil})
				return
			}
			_ = json.NewEncoder(w).Encode(driveFileList{Files: []driveListedFile{{ID: "file-lost", Name: "empty.bin", Size: "0", MD5Checksum: emptyBlobMD5}}})
		case http.MethodPost:
			// Simulate an ambiguous transport outcome by abruptly failing after
			// the server logically accepted the create. A synthetic 500 is enough
			// to exercise the reconciliation branch deterministically.
			w.WriteHeader(http.StatusInternalServerError)
		default:
			t.Fatalf("method=%s", r.Method)
		}
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client(), AccessToken: "token", UploadEndpoint: server.URL + "/upload?uploadType=resumable"}
	file, err := client.CreateOrAdoptEmpty(context.Background(), "empty.bin", "parent-1")
	if err != nil {
		t.Fatal(err)
	}
	if file.FileID != "file-lost" || file.MD5Checksum != emptyBlobMD5 {
		t.Fatalf("file=%+v", file)
	}
}

func TestCreateOrAdoptEmptyRejectsSameNameConflict(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(driveFileList{Files: []driveListedFile{{ID: "wrong", Name: "empty.bin", Size: "1", MD5Checksum: "c4ca4238a0b923820dcc509a6f75849b"}}})
	}))
	defer server.Close()

	client := &driveResumableHTTP{Client: server.Client(), AccessToken: "token", UploadEndpoint: server.URL + "/upload?uploadType=resumable"}
	if _, err := client.CreateOrAdoptEmpty(context.Background(), "empty.bin", "parent-1"); err == nil {
		t.Fatal("expected same-name conflict")
	}
}
