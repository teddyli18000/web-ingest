package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
)

func TestMasterPersistsServerRotatedBaiduCookie(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Cookie") == "" {
			t.Error("Baidu session cookie was not sent")
		}
		w.Header().Add("Set-Cookie", "STOKEN=renewed-session; Path=/")
		w.Header().Set("Content-Type", "text/html")
		_, _ = w.Write([]byte("<html>not a valid share</html>"))
	}))
	defer server.Close()

	store := baidu.CookieStore{Path: filepath.Join(t.TempDir(), "session.cookies")}
	initial := "BDUSS=original; STOKEN=old-session"
	if err := store.Save(initial); err != nil {
		t.Fatal(err)
	}
	client, err := newTrackedBaiduClient(initial, store, baidu.WithBaseURL(server.URL))
	if err != nil {
		t.Fatal(err)
	}
	link, err := baidu.ParseShareLink("https://pan.baidu.com/s/1abcdef")
	if err != nil {
		t.Fatal(err)
	}
	_, _ = client.AccessSharePage(context.Background(), link)
	updated, err := store.Load()
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(updated, "BDUSS=original") || !strings.Contains(updated, "STOKEN=renewed-session") {
		t.Fatalf("session jar did not preserve server rotation")
	}
}

func TestMasterDoesNotPersistCookiesMissingLoginPair(t *testing.T) {
	store := baidu.CookieStore{Path: filepath.Join(t.TempDir(), "session.cookies")}
	client, err := newTrackedBaiduClient("", store)
	if err != nil {
		t.Fatal(err)
	}
	if err := client.after(nil); err != nil {
		t.Fatal(err)
	}
	text, err := store.Load()
	if err != nil {
		t.Fatal(err)
	}
	if text != "" {
		t.Fatal("persisted a non-login browser cookie")
	}
}
