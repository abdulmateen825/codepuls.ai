package com.codepulse.scan;

import java.util.List;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.repository.RepositoryRepository;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.domain.ScanEntity;
import com.codepulse.scan.dto.FindingPageResponse;
import com.codepulse.scan.dto.FindingResponse;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanSummaryResponse;

@Service
public class ScanService {

    private final RepositoryRepository repositoryRepository;
    private final ScanRepository scanRepository;
    private final FindingRepository findingRepository;
    private final AiServiceClient aiServiceClient;

    public ScanService(
            RepositoryRepository repositoryRepository,
            ScanRepository scanRepository,
            FindingRepository findingRepository,
            AiServiceClient aiServiceClient) {
        this.repositoryRepository = repositoryRepository;
        this.scanRepository = scanRepository;
        this.findingRepository = findingRepository;
        this.aiServiceClient = aiServiceClient;
    }

    @Transactional
    public ScanDetailResponse startScan(UUID repositoryId, User currentUser) {
        requireAuthenticated(currentUser);
        RepositoryEntity repository = findRepositoryForAccess(repositoryId, currentUser);

        ScanEntity scan = scanRepository.save(new ScanEntity(repository));
        try {
            aiServiceClient.dispatchScan(scan.getId(), repository.getId(), repository.getGithubUrl());
        } catch (RuntimeException exception) {
            scan.markFailed("AI dispatch failed.");
        }

        return ScanDetailResponse.from(scan);
    }

    @Transactional(readOnly = true)
    public List<ScanSummaryResponse> getRepositoryScans(UUID repositoryId, User currentUser) {
        requireAuthenticated(currentUser);
        RepositoryEntity repository = findRepositoryForAccess(repositoryId, currentUser);

        return scanRepository.findAllByRepositoryOrderByCreatedAtDesc(repository)
                .stream()
                .map(ScanSummaryResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public ScanDetailResponse getScan(UUID scanId, User currentUser) {
        ScanEntity scan = findScanForAccess(scanId, currentUser);
        return ScanDetailResponse.from(scan);
    }

    @Transactional(readOnly = true)
    public FindingPageResponse getFindings(
            UUID scanId,
            String severity,
            String category,
            Pageable pageable,
            User currentUser) {
        ScanEntity scan = findScanForAccess(scanId, currentUser);
        Page<FindingResponse> findings = findingRepository.findByScanWithFilters(
                scan,
                normalizeFilter(severity),
                normalizeFilter(category),
                pageable)
                .map(FindingResponse::from);

        return FindingPageResponse.from(findings);
    }

    private RepositoryEntity findRepositoryForAccess(UUID repositoryId, User currentUser) {
        RepositoryEntity repository = repositoryRepository.findById(repositoryId)
                .orElseThrow(() -> ApiException.notFound("Repository was not found."));

        if (!repository.getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this repository.");
        }

        return repository;
    }

    private ScanEntity findScanForAccess(UUID scanId, User currentUser) {
        requireAuthenticated(currentUser);
        ScanEntity scan = scanRepository.findById(scanId)
                .orElseThrow(() -> ApiException.notFound("Scan was not found."));

        if (!scan.getRepository().getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this scan.");
        }

        return scan;
    }

    private String normalizeFilter(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }

        return value.trim();
    }

    private void requireAuthenticated(User currentUser) {
        if (currentUser == null) {
            throw ApiException.unauthorized("Authentication is required.");
        }
    }
}
