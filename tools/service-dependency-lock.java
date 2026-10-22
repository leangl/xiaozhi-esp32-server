// JDK-only verifier/fetcher. The build never runs Maven until all inputs pass.
// Usage: java service-dependency-lock.java fetch|verify LOCK DIRECTORY BASE [SOURCE]
import java.io.*;
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.security.*;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

class ServiceDependencyLock {
    record Artifact(String sha, long size, String name, URI uri) {}
    static final Set<String> HOSTS = Set.of("repo.maven.apache.org", "deb.debian.org", "security.debian.org", "snapshot.debian.org", "packages.bell-sw.com");
    static String hash(Path path) throws Exception {
        var digest = MessageDigest.getInstance("SHA-256");
        try (var input = Files.newInputStream(path)) {
            byte[] buffer = new byte[1024 * 1024];
            for (int n; (n = input.read(buffer)) != -1;) digest.update(buffer, 0, n);
        }
        return HexFormat.of().formatHex(digest.digest());
    }
    static String safe(String name) {
        var path = Path.of(name);
        if (name.isEmpty() || path.isAbsolute() || !path.normalize().toString().equals(name) || name.contains("\\") || Arrays.asList(name.split("/")).contains("..")) throw new IllegalArgumentException("Unsafe lock path");
        return name;
    }
    static void verify(List<Artifact> artifacts, Path directory) throws Exception {
        var expected = new TreeSet<String>();
        for (var artifact : artifacts) expected.add(artifact.name);
        var actual = new TreeSet<String>();
        try (var paths = Files.walk(directory)) {
            for (var path : paths.toList()) {
                if (Files.isSymbolicLink(path)) throw new IllegalArgumentException("Symlink in artifact repository");
                if (Files.isRegularFile(path)) actual.add(directory.relativize(path).toString());
            }
        }
        if (!expected.equals(actual)) throw new IllegalArgumentException("Missing/unreviewed artifact(s)");
        for (var artifact : artifacts) {
            var path = directory.resolve(artifact.name);
            if (Files.size(path) != artifact.size || !hash(path).equals(artifact.sha)) throw new IllegalArgumentException("Artifact hash/size mismatch: " + artifact.name);
        }
    }
    public static void main(String[] args) throws Exception {
        if (args.length < 4 || args.length > 5 || !Set.of("fetch", "verify").contains(args[0])) throw new IllegalArgumentException("Expected fetch|verify LOCK DIRECTORY BASE [SOURCE]");
        var lines = Files.readAllLines(Path.of(args[1]));
        if (lines.isEmpty() || !lines.getFirst().equals("service-dependency-lock-v1")) throw new IllegalArgumentException("Unknown lock format");
        var artifacts = new ArrayList<Artifact>();
        var metadata = new HashMap<String, String>();
        var names = new HashSet<String>();
        var inputs = new HashSet<String>();
        for (var line : lines.subList(1, lines.size())) {
            var row = line.split("\t", -1);
            switch (row[0]) {
                case "kind", "base", "arch" -> {
                    if (row.length != 2 || metadata.put(row[0], row[1]) != null) throw new IllegalArgumentException("Invalid metadata");
                }
                case "input" -> {
                    if (row.length != 3 || args.length != 5 || !inputs.add(safe(row[2]))) throw new IllegalArgumentException("Invalid source input");
                    var path = Path.of(args[4]).resolve(row[2]);
                    if (Files.isSymbolicLink(path) || !hash(path).equals(row[1])) throw new IllegalArgumentException("Maven declaration changed: " + row[2]);
                }
                case "installed" -> { if (row.length != 3) throw new IllegalArgumentException("Invalid installed row"); }
                case "artifact" -> {
                    if (row.length != 6 || !row[1].matches("[a-f0-9]{64}") || !names.add(safe(row[3]))) throw new IllegalArgumentException("Invalid/duplicate artifact");
                    var uri = URI.create(row[4]);
                    if (!"https".equals(uri.getScheme()) || !HOSTS.contains(uri.getHost()) || uri.getUserInfo() != null || uri.getPort() != -1 || uri.getQuery() != null || uri.getFragment() != null) throw new IllegalArgumentException("Unapproved artifact URL");
                    long size = Long.parseLong(row[2]);
                    if (size <= 0) throw new IllegalArgumentException("Invalid artifact size");
                    artifacts.add(new Artifact(row[1], size, row[3], uri));
                }
                default -> throw new IllegalArgumentException("Malformed lock row");
            }
        }
        if (artifacts.isEmpty() || !args[3].equals(metadata.get("base")) || !args[3].matches("docker.io/[^\\s]+@sha256:[a-f0-9]{64}") || !Set.of("maven", "deb", "apk").contains(metadata.getOrDefault("kind", ""))) throw new IllegalArgumentException("Incomplete/stale base lock");
        if ("maven".equals(metadata.get("kind")) && (!inputs.equals(Set.of("pom.xml", ".mvn/settings.xml", ".mvn/maven.config")) || !"aarch64".equals(System.getProperty("os.arch")))) throw new IllegalArgumentException("Maven inputs/architecture differ from lock");
        var directory = Path.of(args[2]);
        if (args[0].equals("fetch")) {
            Files.createDirectories(directory);
            try (var entries = Files.list(directory)) { if (entries.findAny().isPresent()) throw new IllegalArgumentException("Fetch destination must be empty"); }
            var client = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NEVER).connectTimeout(Duration.ofSeconds(45)).proxy(new ProxySelector() {
                public List<Proxy> select(URI uri) { return List.of(Proxy.NO_PROXY); }
                public void connectFailed(URI uri, SocketAddress address, IOException error) {}
            }).build();
            try (var executor = Executors.newFixedThreadPool(12)) {
                var futures = new ArrayList<Future<?>>();
                for (var artifact : artifacts) futures.add(executor.submit(() -> {
                    var target = directory.resolve(artifact.name);
                    var partial = target.resolveSibling(target.getFileName() + ".partial");
                    try {
                        Files.createDirectories(target.getParent());
                        var request = HttpRequest.newBuilder(artifact.uri).timeout(Duration.ofSeconds(120)).GET().build();
                        var response = client.send(request, HttpResponse.BodyHandlers.ofInputStream());
                        try (var stream = response.body(); var out = Files.newOutputStream(partial, StandardOpenOption.CREATE_NEW)) {
                            if (response.statusCode() != 200) throw new IOException("Artifact HTTP status " + response.statusCode() + ": " + artifact.name);
                            long count = 0;
                            byte[] buffer = new byte[1024 * 1024];
                            for (int n; (n = stream.read(buffer)) != -1;) {
                                count += n;
                                if (count > artifact.size) throw new IOException("Artifact exceeds locked size: " + artifact.name);
                                out.write(buffer, 0, n);
                            }
                        }
                        if (Files.size(partial) != artifact.size || !hash(partial).equals(artifact.sha)) throw new IOException("Artifact hash/size mismatch: " + artifact.name);
                        Files.move(partial, target);
                    } catch (Exception error) { throw new CompletionException(error); }
                    finally { try { Files.deleteIfExists(partial); } catch (IOException ignored) {} }
                }));
                for (var future : futures) future.get();
            }
        }
        verify(artifacts, directory);
        System.out.println("Dependency lock: " + args[0] + " passed (" + artifacts.size() + " artifacts)");
    }
}
