package com.codepulse.system.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.codepulse.system.dto.HealthStatusResponse;
import com.codepulse.system.service.SystemHealthService;

@RestController
@RequestMapping("/api")
public class SystemHealthController {

    private final SystemHealthService systemHealthService;

    public SystemHealthController(SystemHealthService systemHealthService) {
        this.systemHealthService = systemHealthService;
    }

    @GetMapping("/health")
    public HealthStatusResponse getCoreHealth() {
        return systemHealthService.getCoreHealth();
    }

    @GetMapping("/system/ai-health")
    public HealthStatusResponse getAiHealth() {
        return systemHealthService.getAiHealth();
    }
}
