package com.codepulse;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

class BackendCoreApplicationTests {

    @Test
    void applicationClassIsLoadable() {
        assertThat(BackendCoreApplication.class).isNotNull();
    }
}
