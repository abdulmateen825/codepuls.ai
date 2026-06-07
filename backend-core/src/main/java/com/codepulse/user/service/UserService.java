package com.codepulse.user.service;

import org.springframework.stereotype.Service;

import com.codepulse.auth.dto.AuthUserResponse;
import com.codepulse.auth.entity.User;
import com.codepulse.common.exception.ApiException;

@Service
public class UserService {

    public AuthUserResponse getCurrentUser(User user) {
        if (user == null) {
            throw ApiException.unauthorized("Authentication is required.");
        }

        return AuthUserResponse.from(user);
    }
}
