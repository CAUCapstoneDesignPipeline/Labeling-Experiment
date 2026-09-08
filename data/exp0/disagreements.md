# 불일치 유닛 — 회의 안건

1단계 83건 / 2단계 2건

합의 라벨은 실험 B 정답용으로만 쓴다. **κ 는 합의 전 원본 라벨로 계산한다.**

- `guava-5773-005` (1단계) A:N / B:N / C:D
    Might it be possible to add a stable version?
- `guava-5773-012` (1단계) A:N / B:N / C:D
    If the sort were stable I'd expect to see `C 1` before `C 2` because that's the order they appear in the input.
- `guava-5773-014` (1단계) A:D / B:N / C:D
    @msmerc: okay, please assign this issue to me.
- `guava-5773-016` (1단계) A:D / B:N / C:D
    I would like to work on this issue.
- `guava-5773-018` (1단계) A:D / B:N / C:D
    Therefore, I need some guidance.
- `guava-5773-019` (1단계) A:D / B:N / C:D
    Could you please give me more information about this issue?
- `guava-5773-022` (1단계) A:D / B:N / C:D
    @tanmauec  see comment here: ⟦URL⟧
- `guava-5773-025` (1단계) A:D / B:N / C:D
    My solution is to generate a comparable such that objects are equal (using the original comparator) it will compare the position in the init
- `guava-5773-026` (1단계) A:D / B:N / C:D
    Is this something you'd want in the main library?
- `guava-5773-033` (1단계) A:D / B:N / C:D
    I see no reason NOT to make `mergeSorted` stable, and certainly no reason to add a separate stable form of it.
- `guava-5773-034` (1단계) A:D / B:N / C:D
    Any performance impact would surely be small.
- `guava-5773-035` (1단계) A:D / B:N / C:D
    Tied elements coming out in a different order might temporarily make a unit test or two fail, but seems unlikely to present a real problem b
- `guava-5773-036` (1단계) A:D / B:N / C:D
    The first PR that would be useful would have test cases that illustrate the problem -- this is unorthodox, but yes, I mean they actually ver
- `guava-5773-037` (1단계) A:D / B:N / C:D
    By default I would assume that we want to find a good variety of these test cases, but if we are convinced that all the cases follow the sam
- `guava-5773-039` (1단계) A:D / B:N / C:D
    We would pull that and then the next PR could simultaneously make the method stable and change the tests just added accordingly.
- `guava-8158-001` (1단계) A:D / B:N / C:N
    forString() incorrectly parsing IPv4 mapped IPv6 address
- `guava-8158-002` (1단계) A:D / B:N / C:N
    When parsing an IPv4 mapped IPv6 address the InetAddresses.forString() incorrectly returns the address as a v4 address.
- `guava-8158-004` (1단계) A:D / B:D / C:N
    Returned as an IPv4 object com.google.common.net
- `guava-8158-006` (1단계) A:D / B:N / C:D
    Can you give me your analysis of the tradeoffs here?
- `guava-8158-007` (1단계) A:D / B:N / C:D
    As a starting point, I asked Gemini, and I got the response below:
- `guava-8158-008` (1단계) A:D / B:N / C:D
    Here is a breakdown of the architectural and practical arguments for both approaches.
- `guava-8158-010` (1단계) A:D / B:N / C:D
    Before weighing the arguments, it is helpful to visualize the structure.
- `guava-8158-011` (1단계) A:D / B:N / C:D
    These addresses are defined in RFC 4291.
- `guava-8158-012` (1단계) A:D / B:D / C:N
    They consist of 80 bits of zeros, 16 bits of ones, and then the 32 bits of the IPv4 address.
- `guava-8158-015` (1단계) A:D / B:N / C:D
    Most standard libraries (like Python's ipaddress or Go's net package) often lean this way because, technically, the input is 128 bits long.
- `guava-8158-016` (1단계) A:D / B:N / C:N
    Data Fidelity (Losslessness): If the input string was ::ffff:192.0.2.1, returning an IPv4 object (192.0.2.1) discards information. You have 
- `guava-8158-017` (1단계) A:D / B:N / C:D
    Socket API Consistency: In dual-stack socket programming, the operating system kernel often exposes these addresses as AF_INET6 (IPv6 family
- `guava-8158-018` (1단계) A:D / B:N / C:D
    Avoids Ambiguity: If the library converts mapped addresses to IPv4, but not compatible addresses (::192.0.2.1, which is deprecated but exist
- `guava-8158-019` (1단계) A:D / B:N / C:D
    Security (Canonicalization): Automatic unmapping can be dangerous. If an Access Control List (ACL) blocks ::ffff:10.0.0.1 but allows 10.0.0.
- `guava-8158-022` (1단계) A:D / B:N / C:D
    Usability & Developer Intent: When a developer parses ::ffff:192.168.1.1, they usually want to know "Which machine is this?" The answer is t
- `guava-8158-023` (1단계) A:D / B:N / C:D
    Protocol Reality: An IPv4-mapped address is not valid for global IPv6 routing. It will never appear in an IPv6 packet header on the wire; it
- `guava-8158-024` (1단계) A:D / B:N / C:D
    Database Compatibility: If you are storing IP addresses in a database column typed for IPv4 (e.g., PostgreSQL inet or a VARCHAR(15)), return
- `guava-8158-026` (1단계) A:D / B:N / C:D
    The "Hybrid" Solution Many modern libraries solve this by returning an IPv6 object but providing a helper method. For example:
- `guava-8158-027` (1단계) A:D / B:N / C:N
    Return IPv6 by default: To maintain structural correctness.
- `guava-8158-028` (1단계) A:D / B:N / C:N
    Provide properties: Such as .ipv4_mapped (boolean) or .teredo (boolean).
- `guava-8158-029` (1단계) A:D / B:N / C:N
    Provide a method: Such as .map_to_ipv4() or .unwrap() which explicitly converts it to the IPv4 object if valid.
- `guava-8158-031` (1단계) A:D / B:N / C:D
    I dug up a comment in some long-deleted code that suggests that `InetAddress.getByAddress` might autoconvert.
- `guava-8158-032` (1단계) A:D / B:N / C:D
    If that's the case, then that would be one argument in favor of making our method do the same.
- `guava-8158-033` (1단계) A:D / B:N / C:D
    This does seem to be the behavior of the JDK `InetAddress.getByAddress`, as well as that of `InetAddress.ofLiteral`, whose behavior is proba
- `guava-8158-035` (1단계) A:D / B:N / C:N
    It's problematic because it is a valid IPv6 address, as reported by the device, but the current net library's behavior makes it effectively 
- `guava-8158-041` (1단계) A:D / B:N / C:D
    The only way I've found so far to force the creation of an `Inet6Address` is to pass a scope ID (or presumably `NetworkInterface`), but that
- `guava-8158-043` (1단계) A:D / B:N / C:D
    I looked into this and found that the current behavior appears to be intentional - there's an existing test at `InetAddressesTest.java:465` 
- `guava-8158-044` (1단계) A:D / B:N / C:N
    For @wdec's use case, `isMappedIPv4Address()` can detect these addresses before parsing:
- `guava-8158-045` (1단계) A:D / B:N / C:D
    Given that (1) this matches JDK behavior, (2) normalizing is safer for ACL comparisons, and (3) a workaround exists, this seems like "workin
- `guava-8158-046` (1단계) A:D / B:N / C:D
    It seems pretty clear to me that the behavior is intentional and, for better or worse, matches the way `InetAddress` chooses to handle these
- `guava-8158-047` (1단계) A:D / B:N / C:D
    There's a pretty long section in the class Javadoc specifically addressing this behavior.
- `vert.x-3786-005` (1단계) A:N / B:D / C:D
    The shared worker pool name can be reused
- `vert.x-3856-001` (1단계) A:N / B:N / C:D
    filesystem api: expose file locking operations
- `vert.x-4487-001` (1단계) A:D / B:N / C:N
    NPE when NetSocket.upgradeToSsl() is called if no TLS configuration in NetClientOptions
- `vert.x-4487-002` (1단계) A:D / B:N / C:N
    When there is no TLS related configuration specified in the NetClientOptions, and user tries to call `NetSocket.upgradeToSsl(handler)`, the 
- `vert.x-4487-003` (1단계) A:D / B:N / C:D
    This also leads to some CI failures in other components, like:
- `vert.x-4487-004` (1단계) A:D / B:N / C:N
    The `sslProvider` in SSLHelper may be `Future.succeededFuture()` which will make `Supplier<SslContextFactory>` is null, so nothing to supply
- `vert.x-4487-006` (1단계) A:D / B:N / C:D
    The following test hangs and fails:
- `vert.x-4660-001` (1단계) A:D / B:D / C:N
    WebSocket fetch and ping / pong
- `vert.x-4660-002` (1단계) A:D / B:N / C:N
    In looking at the fabric8 integration of vert.x we are using pause / fetch on websockets to control the rate at which messages are processed
- `vert.x-4660-003` (1단계) A:D / B:D / C:N
    However it appears that ping / pong messages from the server count towards the fetch.
- `vert.x-4660-004` (1단계) A:D / B:D / C:N
    We can workaround this by not sending pings ourselves, or if we ever need to, use a pongHandler to increase the fetch.
- `vert.x-4660-005` (1단계) A:D / B:N / C:D
    However if the server sends a ping since the ping handling is baked-in there's nothing we can do to increase the fetch.
- `vert.x-4660-006` (1단계) A:D / B:N / C:N
    If we remove the pause / fetch, this will complete as expected.
- `vert.x-4660-007` (1단계) A:D / B:N / C:D
    cc @vietj the current api server implementation does not send a ping, so this isn't an issue for fabric8 yet.
- `vert.x-4660-008` (1단계) A:D / B:N / C:N
    However the likely resolution of the upstream issue ⟦URL⟧ will include using ping / pong as the heartbeat mechanism for websockets, so we'll
- `vert.x-4660-009` (1단계) A:D / B:D / C:N
    Need a specific PR for 4.x
- `vert.x-5748-001` (1단계) A:D / B:N / C:N
    NetSocket.endHandler called too early before all data is read (fires with closeHandler)
- `vert.x-5748-002` (1단계) A:D / B:D / C:N
    When using NetSocket with flow control (pause() / resume()), the endHandler is sometimes invoked too early, before all buffered data has bee
- `vert.x-5748-003` (1단계) A:D / B:N / C:D
    According to the Javadoc), the endHandler should be called after all data has been read, and possibly even after the closeHandler only if th
- `vert.x-5748-004` (1단계) A:D / B:N / C:N
    However, in Vert.x 5.x (4.5.x is good), the endHandler is triggered at the same time as the closeHandler, effectively before all data is dra
- `vert.x-5748-005` (1단계) A:N / B:D / C:N
    Create a simple TCP server that sends a large data block (e.g. ≥ 1 MB) and then closes the connection.
- `vert.x-5748-006` (1단계) A:N / B:D / C:N
    Create a client that connects and reads with flow control
- `vert.x-6006-001` (1단계) A:D / B:N / C:D
    Typo in the HTTP header documentation
- `vert.x-6006-004` (1단계) A:D / B:N / C:D
    but actually second sentence should contain HTTP/2
- `vert.x-6276-001` (1단계) A:D / B:N / C:D
    Shared HTTP client incorrect reference counting
- `vert.x-6276-002` (1단계) A:D / B:D / C:N
    The shared HTTP client has a regression where closing one of its client, will close the underlying client, instead of updating the reference
- `vert.x-6294-001` (1단계) A:D / B:D / C:N
    Resetting a completed HTTP/1.1 request closes a pooled connection after reuse
- `vert.x-6294-002` (1단계) A:D / B:D / C:N
    An HTTP/1.1 HttpClientRequest can retain access to its former connection after the request has completed.
- `vert.x-6294-003` (1단계) A:D / B:N / C:N
    If the connection returns to the pool and is assigned to a newer request, calling reset() on the completed request closes the physical conne
- `vert.x-6294-005` (1단계) A:D / B:D / C:N
    The subsequent request fails with io.vertx.core.http.HttpClosedException: Connection was closed.
- `vert.x-6294-006` (1단계) A:D / B:D / C:N
    Http1xClientConnection.reset() uses responses.contains(stream) || stream.responseEnded to decide that a stream is in flight. responseEnded r
- `vert.x-6294-007` (1단계) A:D / B:D / C:N
    A late reset therefore marks the physical connection for closure after it has been reused.
- `vert.x-6294-008` (1단계) A:D / B:D / C:N
    The attached focused Http1xTest uses one keep-alive connection with pipelining disabled.
- `vert.x-6294-009` (1단계) A:D / B:N / C:N
    Request A completes, Request B reuses the connection, and reset() is called on A while B is active.
- `vert.x-6294-010` (1단계) A:D / B:N / C:D
    Expect: 100-continue makes the sequence deterministic; the underlying issue is not specific to 100 Continue.
- `vert.x-6294-014` (1단계) A:D / B:N / C:D
    Run: mvn -Dtest=io.vertx.core.http.Http1xTest#testResetCompletedRequestDoesNotCloseReusedExpectContinueRequest test
- `vert.x-6294-016` (1단계) A:D / B:D / C:N
    The equivalent behavior passes on the 4.2.6 code line and fails on the 4.4.1 and 4.5.31 code lines. vertx-4531-reset-completed-request-repro
- `guava-5773-001` (2단계) A:L / B:E / C:E
    Make `Iterators.mergeSorted()` stable
- `vert.x-3856-002` (2단계) A:S / B:E / C:S
    The `lock` and `tryLock` methods of `AsynchronousFileChannel` should be made available for `AsyncFile` wrappers, so one can perform proper f