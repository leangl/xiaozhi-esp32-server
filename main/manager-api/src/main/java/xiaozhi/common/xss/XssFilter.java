package xiaozhi.common.xss;

import java.io.IOException;

import org.springframework.util.PathMatcher;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.FilterConfig;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import lombok.AllArgsConstructor;

/**
 * XSS filtering
 * Copyright (c) 人人开源 All rights reserved.
 * Original copyright holder: Renren Open Source; the legal attribution above is retained.
 * Website: https://www.renren.io
 */
@AllArgsConstructor
public class XssFilter implements Filter {
    private final XssProperties properties;
    private final PathMatcher pathMatcher;

    @Override
    public void init(FilterConfig config) throws ServletException {
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest httpServletRequest = (HttpServletRequest) request;

        // Allow through
        if (shouldNotFilter(httpServletRequest)) {
            chain.doFilter(request, response);

            return;
        }

        chain.doFilter(new XssHttpServletRequestWrapper(httpServletRequest), response);
    }

    private boolean shouldNotFilter(HttpServletRequest request) {
        // URLs excluded from filtering
        return properties.getExcludeUrls().stream()
                .anyMatch(excludeUrl -> pathMatcher.match(excludeUrl, request.getServletPath()));
    }

    @Override
    public void destroy() {
    }

}
