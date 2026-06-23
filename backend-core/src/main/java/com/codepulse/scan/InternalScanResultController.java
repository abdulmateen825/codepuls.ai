package com.codepulse.scan;

import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.common.exception.ApiException;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanResultCallbackRequest;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/internal")
public class InternalScanResultController {

    private final ScanService scanService;
    private final String internalApiKey;

    public InternalScanResultController(
            ScanService scanService,
            @Value("${fastapi.internal-api-key}") String internalApiKey) {
        this.scanService = scanService;
        this.internalApiKey = internalApiKey;
    }

    @PostMapping("/scans/{scanId}/results")
    @ResponseStatus(HttpStatus.OK)
    public ScanDetailResponse receiveScanResults(
            @PathVariable UUID scanId,
            @Valid @RequestBody ScanResultCallbackRequest request,
            @RequestHeader(value = HttpHeaders.AUTHORIZATION, required = false) String authorization) {
        requireInternalApiKey(authorization);
        return scanService.applyScanResults(scanId, request);
    }

    private void requireInternalApiKey(String authorization) {
        if (!("Bearer " + internalApiKey).equals(authorization)) {
            throw ApiException.unauthorized("Invalid internal API key.");
        }
    }
}
