// Validation-only harness: copy into a temporary manager-api test source tree.
// Registers controller instances without their service lifecycle. Only the
// generated API description endpoint is called; no business endpoint executes.
package translation.validation;

import java.lang.reflect.Constructor;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.boot.SpringBootConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ClassPathScanningCandidateComponentProvider;
import org.springframework.context.annotation.Import;
import org.springframework.core.type.filter.AnnotationTypeFilter;
import org.springframework.stereotype.Controller;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.beans.factory.annotation.Autowired;
import com.fasterxml.jackson.databind.ObjectMapper;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(classes = OpenApiTranslationValidationTest.Harness.class,
        properties = {"spring.profiles.active=translation-validation",
                "spring.liquibase.enabled=false", "spring.main.banner-mode=off"})
@AutoConfigureMockMvc
public class OpenApiTranslationValidationTest {
    @Autowired MockMvc mvc;
    @Autowired ObjectMapper mapper;

    @Test
    void generateActualSpringdocDescriptionWithoutExternalServices() throws Exception {
        String json = mvc.perform(get("/v3/api-docs"))
                .andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        var tree = mapper.readTree(json);
        assertTrue(tree.path("paths").size() >= 50, "Expected real controller routes");
        assertTrue(tree.path("components").path("schemas").size() >= 20,
                "Expected actual DTO schemas");
        Path output = Path.of(System.getProperty("translation.openapi.output", "/tmp/openapi.json"));
        Files.writeString(output, json);
        System.out.printf("OPENAPI_VALIDATION paths=%d schemas=%d output=%s%n",
                tree.path("paths").size(), tree.path("components").path("schemas").size(), output);
    }

    @SpringBootConfiguration
    @EnableAutoConfiguration(excludeName = {
            "org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration",
            "org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration",
            "org.springframework.boot.autoconfigure.data.redis.RedisRepositoriesAutoConfiguration",
            "com.alibaba.druid.spring.boot3.autoconfigure.DruidDataSourceAutoConfigure",
            "com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration"})
    @Import(xiaozhi.common.config.SwaggerConfig.class)
    static class Harness {
        @Bean
        static BeanFactoryPostProcessor controllersWithoutServiceLifecycle() {
            return factory -> {
                var scanner = new ClassPathScanningCandidateComponentProvider(false);
                scanner.addIncludeFilter(new AnnotationTypeFilter(Controller.class));
                for (var candidate : scanner.findCandidateComponents("xiaozhi")) {
                    try {
                        Class<?> type = Class.forName(candidate.getBeanClassName());
                        Constructor<?> ctor = Arrays.stream(type.getDeclaredConstructors())
                                .min(java.util.Comparator.comparingInt(Constructor::getParameterCount))
                                .orElseThrow();
                        ctor.setAccessible(true);
                        Object[] args = Arrays.stream(ctor.getParameterTypes())
                                .map(parameter -> mock(parameter)).toArray();
                        factory.registerSingleton(type.getName(), ctor.newInstance(args));
                    } catch (ReflectiveOperationException exception) {
                        throw new IllegalStateException("Cannot register API controller", exception);
                    }
                }
            };
        }
    }
}
