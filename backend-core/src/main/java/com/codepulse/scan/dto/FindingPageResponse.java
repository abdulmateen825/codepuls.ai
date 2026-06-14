package com.codepulse.scan.dto;

import java.util.List;

import org.springframework.data.domain.Page;

public record FindingPageResponse(
        List<FindingResponse> content,
        long totalElements,
        int totalPages,
        int page,
        int size) {

    public static FindingPageResponse from(Page<FindingResponse> findings) {
        return new FindingPageResponse(
                findings.getContent(),
                findings.getTotalElements(),
                findings.getTotalPages(),
                findings.getNumber(),
                findings.getSize());
    }
}
