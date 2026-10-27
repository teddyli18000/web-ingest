package main

import (
	"encoding/base64"
	"strings"
	"testing"
)

func testStateKey(fill byte) string {
	return base64.StdEncoding.EncodeToString([]byte(strings.Repeat(string([]byte{fill}), 32)))
}

func TestSealCapabilityRoundTrip(t *testing.T) {
	key := testStateKey('a')
	sealed, err := sealCapability(key, "task-1", "file-1", "https://upload.example/session-secret")
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(sealed, "session-secret") || !strings.HasPrefix(sealed, "v1.") {
		t.Fatalf("unexpected sealed value %q", sealed)
	}
	opened, err := openCapability(key, "task-1", "file-1", sealed)
	if err != nil {
		t.Fatal(err)
	}
	if opened != "https://upload.example/session-secret" {
		t.Fatalf("opened=%q", opened)
	}
}

func TestSealCapabilityIsBoundToTaskAndFile(t *testing.T) {
	key := testStateKey('b')
	sealed, err := sealCapability(key, "task-1", "file-1", "secret")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := openCapability(key, "task-1", "file-2", sealed); err == nil {
		t.Fatal("expected file binding failure")
	}
	if _, err := openCapability(key, "task-2", "file-1", sealed); err == nil {
		t.Fatal("expected task binding failure")
	}
}

func TestSealCapabilityRejectsWrongKeyAndTamper(t *testing.T) {
	sealed, err := sealCapability(testStateKey('c'), "task", "file", "secret")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := openCapability(testStateKey('d'), "task", "file", sealed); err == nil {
		t.Fatal("expected wrong key failure")
	}
	parts := strings.Split(sealed, ".")
	parts[2] = parts[2][:len(parts[2])-1] + "A"
	if _, err := openCapability(testStateKey('c'), "task", "file", strings.Join(parts, ".")); err == nil {
		t.Fatal("expected tamper failure")
	}
}

func TestDecodeStateKeyRequiresExactAES256Key(t *testing.T) {
	short := base64.StdEncoding.EncodeToString(make([]byte, 31))
	if _, err := decodeStateKey(short); err == nil {
		t.Fatal("expected short key failure")
	}
	if _, err := decodeStateKey("not-base64"); err == nil {
		t.Fatal("expected base64 failure")
	}
}
