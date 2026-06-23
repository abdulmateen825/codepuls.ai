package com.codepulse.scan;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.doThrow;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

import org.mockito.ArgumentCaptor;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.util.ReflectionTestUtils;

import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.repository.RepositoryRepository;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;
import com.codepulse.scan.dto.FindingPageResponse;
import com.codepulse.scan.dto.FindingResponse;
import com.codepulse.scan.dto.ScanDetailResponse;
import com.codepulse.scan.dto.ScanResultCallbackRequest;
import com.codepulse.scan.dto.ScanResultFindingRequest;
import com.codepulse.scan.dto.ScanResultScoresRequest;
import com.codepulse.scan.dto.ScanSummaryResponse;
import com.codepulse.scan.dto.StartScanRequest;
import com.codepulse.scan.domain.ScanStatus;
import com.fasterxml.jackson.databind.ObjectMapper;

@ExtendWith(MockitoExtension.class)
class ScanServiceTest {

    @Mock
    private RepositoryRepository repositoryRepository;

    @Mock
    private ScanRepository scanRepository;

    @Mock
    private FindingRepository findingRepository;

    @Mock
    private AiServiceClient aiServiceClient;

    private ScanService scanService;

    @BeforeEach
    void setUp() {
        scanService = new ScanService(
                repositoryRepository,
                scanRepository,
                findingRepository,
                aiServiceClient,
                new ObjectMapper());
    }

    @Test
    void startScanCreatesQueuedScanAndDispatchesAiWork() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        RepositoryEntity repository = repository(repositoryId, owner);
        UUID scanId = UUID.randomUUID();

        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository));
        when(scanRepository.save(any(ScanEntity.class))).thenAnswer(invocation -> {
            ScanEntity scan = invocation.getArgument(0);
            ReflectionTestUtils.setField(scan, "id", scanId);
            return scan;
        });

        ScanDetailResponse response = scanService.startScan(repositoryId, new StartScanRequest("develop"), owner);

        assertThat(response.id()).isEqualTo(scanId);
        assertThat(response.status()).isEqualTo("QUEUED");
        verify(aiServiceClient).dispatchScan(
                scanId,
                repositoryId,
                "https://github.com/codepulse/backend-core",
                "develop");
    }

    @Test
    void startScanDefaultsBranchToMainWhenMissing() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        RepositoryEntity repository = repository(repositoryId, owner);
        UUID scanId = UUID.randomUUID();

        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository));
        when(scanRepository.save(any(ScanEntity.class))).thenAnswer(invocation -> {
            ScanEntity scan = invocation.getArgument(0);
            ReflectionTestUtils.setField(scan, "id", scanId);
            return scan;
        });

        scanService.startScan(repositoryId, new StartScanRequest(null), owner);

        verify(aiServiceClient).dispatchScan(
                scanId,
                repositoryId,
                "https://github.com/codepulse/backend-core",
                "main");
    }

    @Test
    void startScanMarksScanFailedWhenAiDispatchFails() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        RepositoryEntity repository = repository(repositoryId, owner);
        UUID scanId = UUID.randomUUID();

        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository));
        when(scanRepository.save(any(ScanEntity.class))).thenAnswer(invocation -> {
            ScanEntity scan = invocation.getArgument(0);
            ReflectionTestUtils.setField(scan, "id", scanId);
            return scan;
        });
        doThrow(new IllegalStateException("FastAPI unavailable"))
                .when(aiServiceClient)
                .dispatchScan(scanId, repositoryId, "https://github.com/codepulse/backend-core", "main");

        ScanDetailResponse response = scanService.startScan(repositoryId, new StartScanRequest(null), owner);

        assertThat(response.status()).isEqualTo("FAILED");
        assertThat(response.errorMessage()).isEqualTo("AI dispatch failed.");
    }

    @Test
    void startScanRequiresAuthenticatedUser() {
        assertThatThrownBy(() -> scanService.startScan(UUID.randomUUID(), new StartScanRequest(null), null))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("UNAUTHORIZED");
    }

    @Test
    void startScanRejectsRepositoryOwnedByAnotherUser() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        User otherUser = user(UUID.randomUUID(), "other@example.com");
        UUID repositoryId = UUID.randomUUID();
        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository(repositoryId, otherUser)));

        assertThatThrownBy(() -> scanService.startScan(repositoryId, new StartScanRequest(null), owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("FORBIDDEN");
    }

    @Test
    void getRepositoryScansReturnsSummariesForOwnedRepository() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID repositoryId = UUID.randomUUID();
        RepositoryEntity repository = repository(repositoryId, owner);
        ScanEntity scan = scan(UUID.randomUUID(), repository);

        when(repositoryRepository.findById(repositoryId)).thenReturn(Optional.of(repository));
        when(scanRepository.findAllByRepositoryOrderByCreatedAtDesc(repository)).thenReturn(List.of(scan));

        List<ScanSummaryResponse> responses = scanService.getRepositoryScans(repositoryId, owner);

        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).repositoryFullName()).isEqualTo("codepulse/backend-core");
    }

    @Test
    void getScanReturnsDetailsForOwnedScan() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID scanId = UUID.randomUUID();
        ScanEntity scan = scan(scanId, repository(UUID.randomUUID(), owner));
        when(scanRepository.findById(scanId)).thenReturn(Optional.of(scan));

        ScanDetailResponse response = scanService.getScan(scanId, owner);

        assertThat(response.id()).isEqualTo(scanId);
        assertThat(response.repositoryFullName()).isEqualTo("codepulse/backend-core");
    }

    @Test
    void getScanReturnsNotFoundWhenMissing() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID scanId = UUID.randomUUID();
        when(scanRepository.findById(scanId)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> scanService.getScan(scanId, owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("NOT_FOUND");
    }

    @Test
    void getFindingsReturnsPagedFindingsForOwnedScan() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID scanId = UUID.randomUUID();
        ScanEntity scan = scan(scanId, repository(UUID.randomUUID(), owner));
        FindingEntity finding = finding(UUID.randomUUID(), scan);
        PageRequest pageable = PageRequest.of(0, 20);

        when(scanRepository.findById(scanId)).thenReturn(Optional.of(scan));
        when(findingRepository.findByScanWithFilters(scan, "HIGH", "SECURITY", pageable))
                .thenReturn(new PageImpl<>(List.of(finding), pageable, 1));

        FindingPageResponse responses = scanService.getFindings(scanId, " HIGH ", " SECURITY ", pageable, owner);

        assertThat(responses.totalElements()).isEqualTo(1);
        assertThat(responses.content().get(0).severity()).isEqualTo("HIGH");
    }

    @Test
    void getFindingsRejectsScanOwnedByAnotherUser() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        User otherUser = user(UUID.randomUUID(), "other@example.com");
        UUID scanId = UUID.randomUUID();
        when(scanRepository.findById(scanId)).thenReturn(Optional.of(scan(scanId, repository(UUID.randomUUID(), otherUser))));

        assertThatThrownBy(() -> scanService.getFindings(scanId, null, null, PageRequest.of(0, 20), owner))
                .isInstanceOf(ApiException.class)
                .extracting("code")
                .isEqualTo("FORBIDDEN");
    }

    @Test
    void applyScanResultsCompletesScanAndStoresFindings() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID scanId = UUID.randomUUID();
        ScanEntity scan = scan(scanId, repository(UUID.randomUUID(), owner));
        ScanResultCallbackRequest request = new ScanResultCallbackRequest(
                ScanStatus.COMPLETED,
                new ScanResultScoresRequest(91, 82, 76),
                Map.of("totalFindings", 1),
                List.of(new ScanResultFindingRequest(
                        "HIGH",
                        "security",
                        "generic-api-key",
                        "A secret was detected.",
                        "Rotate the secret.",
                        ".env",
                        1,
                        "gitleaks",
                        null)),
                null);

        when(scanRepository.findById(scanId)).thenReturn(Optional.of(scan));

        ScanDetailResponse response = scanService.applyScanResults(scanId, request);

        assertThat(response.status()).isEqualTo("COMPLETED");
        assertThat(response.qualityScore()).isEqualTo(91);
        assertThat(response.securityScore()).isEqualTo(82);
        assertThat(response.maintainabilityScore()).isEqualTo(76);
        verify(findingRepository).deleteByScan(scan);
        ArgumentCaptor<List<FindingEntity>> findingsCaptor = ArgumentCaptor.forClass(List.class);
        verify(findingRepository).saveAll(findingsCaptor.capture());
        assertThat(findingsCaptor.getValue()).hasSize(1);
        assertThat(findingsCaptor.getValue().get(0).getRuleId()).isEqualTo("gitleaks:generic-api-key");
        assertThat(scan.getMetadataJson()).contains("totalFindings");
    }

    @Test
    void applyScanResultsMarksScanFailedAndClearsFindings() {
        User owner = user(UUID.randomUUID(), "owner@example.com");
        UUID scanId = UUID.randomUUID();
        ScanEntity scan = scan(scanId, repository(UUID.randomUUID(), owner));
        ScanResultCallbackRequest request = new ScanResultCallbackRequest(
                ScanStatus.FAILED,
                null,
                Map.of("branch", "main"),
                List.of(),
                "clone failed");

        when(scanRepository.findById(scanId)).thenReturn(Optional.of(scan));

        ScanDetailResponse response = scanService.applyScanResults(scanId, request);

        assertThat(response.status()).isEqualTo("FAILED");
        assertThat(response.errorMessage()).isEqualTo("clone failed");
        verify(findingRepository).deleteByScan(scan);
    }

    private User user(UUID id, String email) {
        User user = new User(email, "password-hash", "Test User");
        ReflectionTestUtils.setField(user, "id", id);
        return user;
    }

    private RepositoryEntity repository(UUID id, User owner) {
        RepositoryEntity repository = new RepositoryEntity(
                owner,
                "https://github.com/codepulse/backend-core",
                "codepulse",
                "backend-core");
        ReflectionTestUtils.setField(repository, "id", id);
        return repository;
    }

    private ScanEntity scan(UUID id, RepositoryEntity repository) {
        ScanEntity scan = new ScanEntity(repository);
        ReflectionTestUtils.setField(scan, "id", id);
        return scan;
    }

    private FindingEntity finding(UUID id, ScanEntity scan) {
        FindingEntity finding = new FindingEntity(
                scan,
                "java:S001",
                "SECURITY",
                "HIGH",
                "Avoid hardcoded secrets",
                "A hardcoded secret was found.",
                "src/main/java/App.java",
                42,
                "String secret = \"value\";",
                "Move secrets into managed configuration.");
        ReflectionTestUtils.setField(finding, "id", id);
        return finding;
    }
}
