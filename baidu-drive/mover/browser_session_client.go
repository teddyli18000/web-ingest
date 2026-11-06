package main

import (
	"context"

	"github.com/teddyli18000/baidu-drive-mover/internal/baidu"
	"github.com/teddyli18000/baidu-drive-mover/internal/manifest"
)

// The master is the only writer of refreshed browser cookies. All its Baidu
// API clients reuse the same runner-local CookieStore between operations.
type trackedBaiduClient struct {
	*baidu.Client
	store baidu.CookieStore
}

func newTrackedBaiduClient(header string, store baidu.CookieStore, opts ...baidu.ClientOption) (*trackedBaiduClient, error) {
	client, err := baidu.NewClient(header, opts...)
	if err != nil {
		return nil, err
	}
	return &trackedBaiduClient{Client: client, store: store}, nil
}

func (c *trackedBaiduClient) after(err error) error {
	if c.HasLoginCookies() {
		latest := c.CookieString()
		previous, readErr := c.store.Load()
		if readErr != nil {
			return readErr
		}
		if latest != previous {
			if saveErr := c.store.Save(latest); saveErr != nil {
				return saveErr
			}
		}
	}
	return err
}

func (c *trackedBaiduClient) AccessSharePage(ctx context.Context, link baidu.ShareLink) (baidu.ShareContext, error) {
	value, err := c.Client.AccessSharePage(ctx, link)
	return value, c.after(err)
}
func (c *trackedBaiduClient) VerifyPassword(ctx context.Context, link baidu.ShareLink, share baidu.ShareContext, password string) error {
	return c.after(c.Client.VerifyPassword(ctx, link, share, password))
}
func (c *trackedBaiduClient) Scan(ctx context.Context, taskID string, link baidu.ShareLink, share baidu.ShareContext, sink manifest.Sink) error {
	return c.after(c.Client.Scan(ctx, taskID, link, share, sink))
}
func (c *trackedBaiduClient) EnsureStagingDirectory(ctx context.Context, remotePath string) error {
	return c.after(c.Client.EnsureStagingDirectory(ctx, remotePath))
}
func (c *trackedBaiduClient) ListStagingDirectory(ctx context.Context, remotePath string) ([]baidu.RemoteFile, error) {
	values, err := c.Client.ListStagingDirectory(ctx, remotePath)
	return values, c.after(err)
}
func (c *trackedBaiduClient) TransferFiles(ctx context.Context, link baidu.ShareLink, share baidu.ShareContext, fsIDs []int64, remotePath string) error {
	return c.after(c.Client.TransferFiles(ctx, link, share, fsIDs, remotePath))
}
func (c *trackedBaiduClient) ListStagingPathForCleanup(ctx context.Context, remotePath string) ([]baidu.RemoteFile, error) {
	values, err := c.Client.ListStagingPathForCleanup(ctx, remotePath)
	return values, c.after(err)
}
func (c *trackedBaiduClient) DeleteStagingPath(ctx context.Context, remotePath string) error {
	return c.after(c.Client.DeleteStagingPath(ctx, remotePath))
}
