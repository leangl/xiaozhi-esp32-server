package xiaozhi.modules.knowledge.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import xiaozhi.modules.knowledge.rag.KnowledgeBaseAdapterFactory;

/**
 * Knowledge base configuration
 * Configure knowledge base beans
 */
@Configuration
public class KnowledgeBaseConfig {

    /**
     * Provide a KnowledgeBaseAdapterFactory bean
     * @return KnowledgeBaseAdapterFactory instance
     */
    @Bean
    public KnowledgeBaseAdapterFactory knowledgeBaseAdapterFactory() {
        return new KnowledgeBaseAdapterFactory();
    }
}
