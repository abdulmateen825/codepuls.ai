package com.codepulse.scan.dto;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record StartScanRequest(
        @Size(max = 120, message = "Branch must be 120 characters or fewer")
        @Pattern(
                regexp = "^[A-Za-z0-9._/-]+$",
                message = "Branch may contain only letters, numbers, dots, underscores, slashes, and hyphens")
        String branch) {

    public String normalizedBranch() {
        if (branch == null || branch.isBlank()) {
            return "main";
        }

        return branch.trim();
    }
}
