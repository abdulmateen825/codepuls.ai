package com.codepulse.report;

import java.util.List;
import java.util.UUID;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.auth.entity.User;
import com.codepulse.report.domain.ReportEntity;
import com.codepulse.report.dto.ReportResponse;

@RestController
@RequestMapping("/api")
public class ReportController {

    private final ReportService reportService;

    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }

    @PostMapping("/scans/{scanId}/reports")
    public ReportResponse createReport(
            @PathVariable UUID scanId,
            @AuthenticationPrincipal User currentUser) {
        return reportService.createReport(scanId, currentUser);
    }

    @GetMapping("/reports")
    public List<ReportResponse> getReports(@AuthenticationPrincipal User currentUser) {
        return reportService.getReports(currentUser);
    }

    @GetMapping("/reports/{reportId}/download")
    public ResponseEntity<ByteArrayResource> downloadReport(
            @PathVariable UUID reportId,
            @AuthenticationPrincipal User currentUser) {
        ReportEntity report = reportService.getReportForDownload(reportId, currentUser);
        ByteArrayResource resource = new ByteArrayResource(report.getContent());

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_PDF)
                .contentLength(report.getSizeBytes())
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + report.getFileName() + "\"")
                .body(resource);
    }
}
