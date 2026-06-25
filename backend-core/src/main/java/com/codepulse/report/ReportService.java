package com.codepulse.report;

import java.util.List;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;
import com.codepulse.integration.ai.AiServiceClient;
import com.codepulse.integration.ai.AiServiceClient.InternalReportFinding;
import com.codepulse.integration.ai.AiServiceClient.InternalReportRequest;
import com.codepulse.report.domain.ReportEntity;
import com.codepulse.report.dto.ReportResponse;
import com.codepulse.scan.FindingRepository;
import com.codepulse.scan.ScanRepository;
import com.codepulse.scan.domain.FindingEntity;
import com.codepulse.scan.domain.ScanEntity;

@Service
public class ReportService {

    private final ScanRepository scanRepository;
    private final FindingRepository findingRepository;
    private final ReportRepository reportRepository;
    private final AiServiceClient aiServiceClient;

    public ReportService(
            ScanRepository scanRepository,
            FindingRepository findingRepository,
            ReportRepository reportRepository,
            AiServiceClient aiServiceClient) {
        this.scanRepository = scanRepository;
        this.findingRepository = findingRepository;
        this.reportRepository = reportRepository;
        this.aiServiceClient = aiServiceClient;
    }

    @Transactional
    public ReportResponse createReport(UUID scanId, User currentUser) {
        requireAuthenticated(currentUser);
        ScanEntity scan = findScanForAccess(scanId, currentUser);
        List<FindingEntity> findings = findingRepository.findAllByScanOrderByCreatedAtDesc(scan);
        byte[] pdf = aiServiceClient.generateReportPdf(toReportRequest(scan, findings));
        String fileName = "codepulse-" + scan.getRepository().getGithubOwner() + "-"
                + scan.getRepository().getGithubName() + "-" + scan.getId() + ".pdf";

        ReportEntity report = reportRepository.save(new ReportEntity(scan, fileName, "application/pdf", pdf));
        return ReportResponse.from(report);
    }

    @Transactional(readOnly = true)
    public List<ReportResponse> getReports(User currentUser) {
        requireAuthenticated(currentUser);
        return reportRepository.findAllByScanRepositoryOwnerIdOrderByCreatedAtDesc(currentUser.getId())
                .stream()
                .map(ReportResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public ReportEntity getReportForDownload(UUID reportId, User currentUser) {
        requireAuthenticated(currentUser);
        ReportEntity report = reportRepository.findById(reportId)
                .orElseThrow(() -> ApiException.notFound("Report was not found."));

        if (!report.getScan().getRepository().getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this report.");
        }

        return report;
    }

    private ScanEntity findScanForAccess(UUID scanId, User currentUser) {
        ScanEntity scan = scanRepository.findById(scanId)
                .orElseThrow(() -> ApiException.notFound("Scan was not found."));

        if (!scan.getRepository().getOwner().getId().equals(currentUser.getId())) {
            throw ApiException.forbidden("You do not have access to this scan.");
        }

        return scan;
    }

    private InternalReportRequest toReportRequest(ScanEntity scan, List<FindingEntity> findings) {
        return new InternalReportRequest(
                scan.getId(),
                scan.getRepository().getId(),
                scan.getRepository().getGithubOwner() + "/" + scan.getRepository().getGithubName(),
                scan.getRepository().getGithubUrl(),
                scan.getStatus().name(),
                scan.getQualityScore(),
                scan.getSecurityScore(),
                scan.getMaintainabilityScore(),
                findings.stream().map(this::toReportFinding).toList());
    }

    private InternalReportFinding toReportFinding(FindingEntity finding) {
        return new InternalReportFinding(
                finding.getSeverity(),
                finding.getCategory(),
                finding.getTitle(),
                finding.getDescription(),
                finding.getRecommendation(),
                finding.getFilePath(),
                finding.getLineNumber(),
                finding.getRuleId());
    }

    private void requireAuthenticated(User currentUser) {
        if (currentUser == null) {
            throw ApiException.unauthorized("Authentication is required.");
        }
    }
}
