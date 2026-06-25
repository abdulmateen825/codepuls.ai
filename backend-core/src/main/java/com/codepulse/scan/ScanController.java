package com.codepulse.scan;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.auth.entity.User;
import com.codepulse.scan.dto.FindingPageResponse;
import com.codepulse.scan.dto.FindingSourceResponse;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanSummaryResponse;
import com.codepulse.scan.dto.StartScanRequest;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api")
public class ScanController {

    private final ScanService scanService;

    public ScanController(ScanService scanService) {
        this.scanService = scanService;
    }

    @PostMapping("/repositories/{repositoryId}/scans")
    @ResponseStatus(HttpStatus.CREATED)
    public ScanDetailResponse startScan(
            @PathVariable UUID repositoryId,
            @AuthenticationPrincipal User currentUser) {
        return scanService.startScan(repositoryId, new StartScanRequest(null), currentUser);
    }

    @PostMapping("/repositories/{repositoryId}/scan")
    @ResponseStatus(HttpStatus.CREATED)
    public ScanDetailResponse startRepositoryScan(
            @PathVariable UUID repositoryId,
            @Valid @RequestBody(required = false) StartScanRequest request,
            @AuthenticationPrincipal User currentUser) {
        return scanService.startScan(
                repositoryId,
                request == null ? new StartScanRequest(null) : request,
                currentUser);
    }

    @GetMapping("/repositories/{repositoryId}/scans")
    public List<ScanSummaryResponse> getRepositoryScans(
            @PathVariable UUID repositoryId,
            @AuthenticationPrincipal User currentUser) {
        return scanService.getRepositoryScans(repositoryId, currentUser);
    }

    @GetMapping("/scans/{scanId}")
    public ScanDetailResponse getScan(
            @PathVariable UUID scanId,
            @AuthenticationPrincipal User currentUser) {
        return scanService.getScan(scanId, currentUser);
    }

    @GetMapping("/scans/{scanId}/findings")
    public FindingPageResponse getFindings(
            @PathVariable UUID scanId,
            @RequestParam(required = false) String severity,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String ruleId,
            @RequestParam(required = false) String smellType,
            @RequestParam(required = false) String language,
            @RequestParam(required = false) String filePath,
            Pageable pageable,
            @AuthenticationPrincipal User currentUser) {
        return scanService.getFindings(
                scanId,
                severity,
                category,
                ruleId,
                smellType,
                language,
                filePath,
                pageable,
                currentUser);
    }

    @GetMapping("/findings/{findingId}/source")
    public FindingSourceResponse getFindingSource(
            @PathVariable UUID findingId,
            @AuthenticationPrincipal User currentUser) {
        return scanService.getFindingSource(findingId, currentUser);
    }
}
