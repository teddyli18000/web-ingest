package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestReconcileExpiredSessionAdoptsUniqueVerifiedObject(t *testing.T) {
	data := []byte("expired-session-source")
	source := &dataRangeSource{data: data}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(driveFileList{Files: []driveListedFile{{
			ID: "drive-file", Name: "file.bin", Size: "22", MD5Checksum: digest(data),
		}}})
	}))
	defer server.Close()
	drive := &driveResumableHTTP{Client: server.Client(), AccessToken: "token", UploadEndpoint: server.URL + "/upload?uploadType=resumable"}
	output, disposition, err := reconcileExpiredSession(context.Background(), source, drive, relayStepInput{
		Name: "file.bin", Size: int64(len(data)), BaiduStagingPath: "/BaiduDriveMover/task/b/file.bin", DriveParentID: "parent",
	})
	if err != nil {
		t.Fatal(err)
	}
	if disposition != expiredSessionAdopted || !output.Complete || output.DriveFileID != "drive-file" || output.ComputedMD5 != digest(data) {
		t.Fatalf("disposition=%q output=%+v", disposition, output)
	}
	if len(source.calls) != 1 || source.calls[0] != [2]int64{0, int64(len(data)) - 1} {
		t.Fatalf("source calls=%+v", source.calls)
	}
}

func TestReconcileExpiredSessionProvesAbsenceWithoutReadingBaidu(t *testing.T) {
	source := &dataRangeSource{data: []byte("abc")}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(driveFileList{Files: nil})
	}))
	defer server.Close()
	drive := &driveResumableHTTP{Client: server.Client(), AccessToken: "token", UploadEndpoint: server.URL + "/upload?uploadType=resumable"}
	_, disposition, err := reconcileExpiredSession(context.Background(), source, drive, relayStepInput{
		Name: "file.bin", Size: 3, BaiduStagingPath: "/BaiduDriveMover/task/b/file.bin", DriveParentID: "parent",
	})
	if err != nil {
		t.Fatal(err)
	}
	if disposition != expiredSessionAbsent || len(source.calls) != 0 {
		t.Fatalf("disposition=%q source calls=%+v", disposition, source.calls)
	}
}

func TestReconcileExpiredSessionRejectsAmbiguousDestination(t *testing.T) {
	data := []byte("abc")
	source := &dataRangeSource{data: data}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_ = json.NewEncoder(w).Encode(driveFileList{Files: []driveListedFile{
			{ID: "a", Name: "file.bin", Size: "3", MD5Checksum: digest(data)},
			{ID: "b", Name: "file.bin", Size: "3", MD5Checksum: digest(data)},
		}})
	}))
	defer server.Close()
	drive := &driveResumableHTTP{Client: server.Client(), AccessToken: "token", UploadEndpoint: server.URL + "/upload?uploadType=resumable"}
	_, _, err := reconcileExpiredSession(context.Background(), source, drive, relayStepInput{
		Name: "file.bin", Size: 3, BaiduStagingPath: "/BaiduDriveMover/task/b/file.bin", DriveParentID: "parent",
	})
	if err == nil || !errorsIs(err, errDriveDestinationConflict) {
		t.Fatalf("expected destination conflict, got %v", err)
	}
}

func errorsIs(err, target error) bool {
	for err != nil {
		if err == target {
			return true
		}
		type unwrapper interface{ Unwrap() error }
		u, ok := err.(unwrapper)
		if !ok {
			return false
		}
		err = u.Unwrap()
	}
	return false
}
