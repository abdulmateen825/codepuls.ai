package com.codepulse.report;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.codepulse.auth.entity.User;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.report.domain.ReportEntity;
import com.codepulse.report.dto.ReportResponse;
import com.codepulse.repository.domain.RepositoryEntity;
import com.codepulse.scan.FindingRepository;
import com.codepulse.scan.ScanRepository;
import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;

@ExtendWith(MockitoExtension.class)
class ReportServiceTest {

    @Mock
    private ScanRepository scanRepository;

    @Mock
    private FindingRepository findingRepository;

    @Mock
    private ReportRepository reportRepository;

    @Mock
    private AiServiceClient aiServiceClient;

    private ReportService reportService;

    @BeforeEach
    void setUp() {
        reportService = new ReportService(scanRepository, findingRepository, reportRepository, aiServiceClient);
    }

    @Test
    void createReportGeneratesPdfAndStoresMetadata() {
        User owner = user(UUID.randomUUID());
        RepositoryEntity repository = repository(UUID.randomUUID(), owner);
        ScanEntity scan = scan(UUID.randomUUID(), repository);
        FindingEntity finding = finding(scan);
        byte[] pdf = "%PDF-1.4\n%%EOF".getBytes();

        when(scanRepository.findById(scan.getId())).thenReturn(Optional.of(scan));
        when(findingRepository.findAllByScanOrderByCreatedAtDesc(scan)).thenReturn(List.of(finding));
        when(aiServiceClient.generateReportPdf(any())).thenReturn(pdf);
        when(reportRepository.save(any(ReportEntity.class))).thenAnswer(invocation -> {
            ReportEntity report = invocation.getArgument(0);
            ReflectionTestUtils.setField(report, "id", UUID.randomUUID());
            return report;
        });

        ReportResponse response = reportService.createReport(scan.getId(), owner);

        assertThat(response.scanId()).isEqualTo(scan.getId());
        assertThat(response.contentType()).isEqualTo("application/pdf");
        assertThat(response.sizeBytes()).isEqualTo((long) pdf.length);
        verify(aiServiceClient).generateReportPdf(any());
    }

    private User user(UUID id) {
        User user = new User("owner@example.com", "password", "Owner");
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

    private FindingEntity finding(ScanEntity scan) {
        return new FindingEntity(
                scan,
                "gitleaks:generic-api-key",
                "security",
                "HIGH",
                "Hardcoded secret",
                "A hardcoded secret was detected.",
                "src/App.java",
                42,
                null,
                "Move the secret into managed configuration.");
    }
}
