package com.codepulse.auth.dto;

import java.time.Instant;
import java.util.UUID;

import com.codepulse.auth.entity.User;

public record AuthUserResponse(
        UUID id,
        String email,
        String fullName,
        String role,
        Instant createdAt) {

    public static AuthUserResponse from(User user) {
        return new AuthUserResponse(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getRole().name(),
                user.getCreatedAt());
    }
}
