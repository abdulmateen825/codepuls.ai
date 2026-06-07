package com.codepulse.user.controller;

import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.auth.dto.AuthUserResponse;
import com.codepulse.auth.entity.User;
import com.codepulse.user.service.UserService;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/me")
    public AuthUserResponse getCurrentUser(@AuthenticationPrincipal User user) {
        return userService.getCurrentUser(user);
    }
}
