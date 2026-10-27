package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"strings"
)

const sealedCapabilityVersion = "v1"

var rawURLBase64 = base64.RawURLEncoding

func decodeStateKey(encoded string) ([]byte, error) {
	encoded = strings.TrimSpace(encoded)
	if encoded == "" {
		return nil, errors.New("state encryption key is not configured")
	}
	key, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil {
		key, err = base64.RawStdEncoding.DecodeString(encoded)
	}
	if err != nil {
		return nil, fmt.Errorf("state encryption key must be base64: %w", err)
	}
	if len(key) != 32 {
		return nil, fmt.Errorf("state encryption key must decode to exactly 32 bytes")
	}
	return key, nil
}

func capabilityAAD(taskID, fileID string) ([]byte, error) {
	taskID = strings.TrimSpace(taskID)
	fileID = strings.TrimSpace(fileID)
	if taskID == "" || fileID == "" {
		return nil, errors.New("task and file IDs are required for capability sealing")
	}
	if strings.ContainsAny(taskID, "\x00\n\r") || strings.ContainsAny(fileID, "\x00\n\r") {
		return nil, errors.New("invalid task or file ID for capability sealing")
	}
	return []byte("baidu-drive/session/v1\x00" + taskID + "\x00" + fileID), nil
}

func sealCapability(encodedKey, taskID, fileID, plaintext string) (string, error) {
	plaintext = strings.TrimSpace(plaintext)
	if plaintext == "" {
		return "", errors.New("capability value is empty")
	}
	key, err := decodeStateKey(encodedKey)
	if err != nil {
		return "", err
	}
	aad, err := capabilityAAD(taskID, fileID)
	if err != nil {
		return "", err
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("initialize AES: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("initialize AES-GCM: %w", err)
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", fmt.Errorf("generate capability nonce: %w", err)
	}
	ciphertext := gcm.Seal(nil, nonce, []byte(plaintext), aad)
	return sealedCapabilityVersion + "." + rawURLBase64.EncodeToString(nonce) + "." + rawURLBase64.EncodeToString(ciphertext), nil
}

func openCapability(encodedKey, taskID, fileID, sealed string) (string, error) {
	key, err := decodeStateKey(encodedKey)
	if err != nil {
		return "", err
	}
	aad, err := capabilityAAD(taskID, fileID)
	if err != nil {
		return "", err
	}
	parts := strings.Split(strings.TrimSpace(sealed), ".")
	if len(parts) != 3 || parts[0] != sealedCapabilityVersion {
		return "", errors.New("unsupported sealed capability format")
	}
	nonce, err := rawURLBase64.DecodeString(parts[1])
	if err != nil {
		return "", errors.New("invalid sealed capability nonce")
	}
	ciphertext, err := rawURLBase64.DecodeString(parts[2])
	if err != nil {
		return "", errors.New("invalid sealed capability ciphertext")
	}
	block, err := aes.NewCipher(key)
	if err != nil {
		return "", fmt.Errorf("initialize AES: %w", err)
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", fmt.Errorf("initialize AES-GCM: %w", err)
	}
	if len(nonce) != gcm.NonceSize() {
		return "", errors.New("invalid sealed capability nonce size")
	}
	plaintext, err := gcm.Open(nil, nonce, ciphertext, aad)
	if err != nil {
		return "", errors.New("sealed capability authentication failed")
	}
	if len(plaintext) == 0 {
		return "", errors.New("sealed capability decrypted to empty value")
	}
	return string(plaintext), nil
}
