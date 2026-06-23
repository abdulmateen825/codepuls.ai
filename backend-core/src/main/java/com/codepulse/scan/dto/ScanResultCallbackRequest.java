package com.codepulse.scan.dto;

import java.util.List;
import java.util.Map;

import com.codepulse.scan.domain.ScanStatus;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record ScanResultCallbackRequest(
        @NotNull
        ScanStatus status,

        @Valid
        ScanResultScoresRequest scores,

        Map<String, Object> metadata,

        @Valid
        List<ScanResultFindingRequest> findings,

        @Size(max = 1000)
        String errorMessage) {

    public List<ScanResultFindingRequest> normalizedFindings() {
        return findings == null ? List.of() : findings;
    }

    public Map<String, Object> normalizedMetadata() {
        return metadata == null ? Map.of() : metadata;
    }
}
