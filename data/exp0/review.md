# 분리 결과 검수

각 유닛이 요구 하나에 대응하는지 확인한다.

```
□ 불릿이 항목별로 쪼개졌는가
□ 코드 안의 마침표에서 잘리지 않았는가
□ 버전 번호에서 잘리지 않았는가
□ 축약어(e.g., i.e.)에서 잘리지 않았는가
□ 한 유닛에 독립된 요구가 2개 이상 들어 있지 않은가
□ 스택 트레이스가 유닛으로 잡히지 않았는가
□ HTML 태그·CSS가 남아 있지 않은가
□ Expected/Actual 헤더가 앞 문장 끝에 붙어 있지 않은가
□ 다른 사람의 코멘트가 앞 유닛에 병합되지 않았는가
```


## google/guava#5773

- `guava-5773-001` (title/title)  Make `Iterators.mergeSorted()` stable
- `guava-5773-002` (body/para)  I've noticed that `Iterators.mergeSorted()` is unstable.
- `guava-5773-003` (body/para)  So for example if I have arrays: `[A_1, B_1, C_1]` `[A_2, B_2, C_2]` (where the comparator looks only at the letter), I'd like the result to iterate `[A_1, A_2,  B_1, B_2,  C_1, C_2]`.
- `guava-5773-004` (body/para)  The current implementation doesn't guarantee this.
- `guava-5773-005` (body/para)  Might it be possible to add a stable version?
- `guava-5773-006` (body/para)  I confess it's not obvious what to do if the arrays are something like `[A_1, A_2, B_1]`, `[A_3]` - to me it would make sense to empty the first iterator of `A_n` elements before moving on to the second, so `[A_1, A_2, A_3, B_1]`.
- `guava-5773-007` (body/para)  [I appreciate I'm being a little lazy with my terminology here - I can provide a fully fleshed example if it's not clear]
- `guava-5773-008` (comment/para)  Could you provide some examples please?
- `guava-5773-009` (comment/para)  [+1 code]  @tuannh982: given a really simple data class:
- `guava-5773-010` (comment/para)  [+2 code]  And the following test: I'd get:
- `guava-5773-011` (comment/para)  Note how `C 2` comes before `C 1`.
- `guava-5773-012` (comment/para)  If the sort were stable I'd expect to see `C 1` before `C 2` because that's the order they appear in the input.
- `guava-5773-013` (comment/para)  Full code here: ⟦URL⟧
- `guava-5773-014` (comment/para)  @msmerc: okay, please assign this issue to me.
- `guava-5773-015` (comment/para)  @chaoren @msmerc  Hello.
- `guava-5773-016` (comment/para)  I would like to work on this issue.
- `guava-5773-017` (comment/para)  But This is my first time contributing to an open-source project.
- `guava-5773-018` (comment/para)  Therefore, I need some guidance.
- `guava-5773-019` (comment/para)  Could you please give me more information about this issue?
- `guava-5773-020` (comment/para)  @HarunSMetin what exactly isn't clear?
- `guava-5773-021` (comment/para)  @msmerc May I know why @tuannh982 's CR couldn't be accepted and issue is still open..?
- `guava-5773-022` (comment/para)  @tanmauec  see comment here: ⟦URL⟧
- `guava-5773-023` (comment/para)  BTW: I'm just the reporter, I have no say in what gets merged or why!
- `guava-5773-024` (comment/para)  @chaoren  / google folk: I've had a go at solving this, see ⟦URL⟧
- `guava-5773-025` (comment/para)  My solution is to generate a comparable such that objects are equal (using the original comparator) it will compare the position in the initial array.
- `guava-5773-026` (comment/para)  Is this something you'd want in the main library?
- `guava-5773-027` (comment/para)  Let me know.
- `guava-5773-028` (comment/para)  Hi, I am new to open source contribution projects.
- `guava-5773-029` (comment/para)  I see that this issue is still open.
- `guava-5773-030` (comment/para)  I was hoping that I could work on it if it has not already been implemented?
- `guava-5773-031` (comment/para)  Can I make a PR?
- `guava-5773-032` (comment/para)  I'm sorry we slept on this issue a while.
- `guava-5773-033` (comment/para)  I see no reason NOT to make `mergeSorted` stable, and certainly no reason to add a separate stable form of it.
- `guava-5773-034` (comment/para)  Any performance impact would surely be small.
- `guava-5773-035` (comment/para)  Tied elements coming out in a different order might temporarily make a unit test or two fail, but seems unlikely to present a real problem beyond that.
- `guava-5773-036` (comment/para)  The first PR that would be useful would have test cases that illustrate the problem -- this is unorthodox, but yes, I mean they actually verify that the problem *does* exist.
- `guava-5773-037` (comment/para)  By default I would assume that we want to find a good variety of these test cases, but if we are convinced that all the cases follow the same simple pattern it might not be necessary.
- `guava-5773-038` (comment/para)  (I'm not even reading the mergeSorted code right now.)
- `guava-5773-039` (comment/para)  We would pull that and then the next PR could simultaneously make the method stable and change the tests just added accordingly.
- `guava-5773-040` (comment/para)  I guess we leave it to you all to fight over who gets to do it?
- `guava-5773-041` (comment/para)  Keep it civil now :-)

## google/guava#8158

- `guava-8158-001` (title/title)  forString() incorrectly parsing IPv4 mapped IPv6 address
- `guava-8158-002` (body/para)  [+1 code]  When parsing an IPv4 mapped IPv6 address the InetAddresses.forString() incorrectly returns the address as a v4 address.
- `guava-8158-003` (body/para)  The address should be returned as a v6 address.
- `guava-8158-004` (body/para)  Returned as an IPv4 object com.google.common.net
- `guava-8158-005` (comment/para)  I'm not sure who the best networking expert for me to ask about this is nowadays.
- `guava-8158-006` (comment/para)  Can you give me your analysis of the tradeoffs here?
- `guava-8158-007` (comment/para)  As a starting point, I asked Gemini, and I got the response below:
- `guava-8158-008` (comment/para)  Here is a breakdown of the architectural and practical arguments for both approaches.
- `guava-8158-009` (comment/para)  What is an IPv4-mapped IPv6 address?
- `guava-8158-010` (comment/para)  Before weighing the arguments, it is helpful to visualize the structure.
- `guava-8158-011` (comment/para)  These addresses are defined in RFC 4291.
- `guava-8158-012` (comment/para)  They consist of 80 bits of zeros, 16 bits of ones, and then the 32 bits of the IPv4 address.
- `guava-8158-013` (comment/para)  They are primarily used to allow IPv6 sockets to communicate with legacy IPv4 nodes.
- `guava-8158-014` (comment/para)  Arguments for Returning an IPv6 Object The "Purist" or "Structural" Approach.
- `guava-8158-015` (comment/para)  Most standard libraries (like Python's ipaddress or Go's net package) often lean this way because, technically, the input is 128 bits long.
- `guava-8158-016` (comment/bullet)  Data Fidelity (Losslessness): If the input string was ::ffff:192.0.2.1, returning an IPv4 object (192.0.2.1) discards information. You have technically altered the data type from what was provided. Returning an IPv6 object preserves the exact state of the input.
- `guava-8158-017` (comment/bullet)  Socket API Consistency: In dual-stack socket programming, the operating system kernel often exposes these addresses as AF_INET6 (IPv6 family). If a library automatically converts them to IPv4, it creates a mismatch between the socket family and the address object, which can cause bugs in low-level networking code.
- `guava-8158-018` (comment/bullet)  Avoids Ambiguity: If the library converts mapped addresses to IPv4, but not compatible addresses (::192.0.2.1, which is deprecated but exists), the behavior becomes unpredictable. Treating all 128-bit inputs as IPv6 is a simpler, more deterministic rule.
- `guava-8158-019` (comment/bullet)  Security (Canonicalization): Automatic unmapping can be dangerous. If an Access Control List (ACL) blocks ::ffff:10.0.0.1 but allows 10.0.0.1, and your parser silently converts the former to the latter, you might accidentally bypass a security rule intended to block IPv6 traffic.
- `guava-8158-020` (comment/para)  Arguments for Returning an IPv4 Object The "Pragmatic" or "Semantic" Approach.
- `guava-8158-021` (comment/para)  This approach argues that the identity of the host is what matters, not the container (the 128-bit format).
- `guava-8158-022` (comment/bullet)  Usability & Developer Intent: When a developer parses ::ffff:192.168.1.1, they usually want to know "Which machine is this?" The answer is the IPv4 host 192.168.1.1. Requiring the developer to manually "unmap" the address every time is cumbersome.
- `guava-8158-023` (comment/bullet)  Protocol Reality: An IPv4-mapped address is not valid for global IPv6 routing. It will never appear in an IPv6 packet header on the wire; it effectively is an IPv4 connection wrapped in an API abstraction. Treating it as IPv4 reflects the actual wire protocol being used.
- `guava-8158-024` (comment/bullet)  Database Compatibility: If you are storing IP addresses in a database column typed for IPv4 (e.g., PostgreSQL inet or a VARCHAR(15)), returning an IPv6 object forces the user to add type-checking logic before saving, whereas an IPv4 object would "just work." Comparison Summary
- `guava-8158-025` (comment/para)  Feature | Return as IPv6 | Return as IPv4 Strictness | High (Structure focused) | Low (Utility focused) Information Loss | None | Loses the ::ffff: prefix Socket Matching | Matches AF_INET6 | Matches AF_INET Best For | Systems programming, Firewalls | Web apps, Analytics, Logging
- `guava-8158-026` (comment/para)  The "Hybrid" Solution Many modern libraries solve this by returning an IPv6 object but providing a helper method. For example:
- `guava-8158-027` (comment/bullet)  Return IPv6 by default: To maintain structural correctness.
- `guava-8158-028` (comment/bullet)  Provide properties: Such as .ipv4_mapped (boolean) or .teredo (boolean).
- `guava-8158-029` (comment/bullet)  Provide a method: Such as .map_to_ipv4() or .unwrap() which explicitly converts it to the IPv4 object if valid.
- `guava-8158-030` (comment/para)  This forces the developer to be explicit about the conversion, mitigating security risks while acknowledging the utility of the underlying IPv4 address.
- `guava-8158-031` (comment/para)  I dug up a comment in some long-deleted code that suggests that `InetAddress.getByAddress` might autoconvert.
- `guava-8158-032` (comment/para)  If that's the case, then that would be one argument in favor of making our method do the same.
- `guava-8158-033` (comment/para)  [+1 code]  This does seem to be the behavior of the JDK `InetAddress.getByAddress`, as well as that of `InetAddress.ofLiteral`, whose behavior is probably nice to match when we can:
- `guava-8158-034` (comment/para)  The particular case where this was observed was when processing data acquired from network devices where some vendors expose an IPv6 address using this notation.
- `guava-8158-035` (comment/para)  It's problematic because it is a valid IPv6 address, as reported by the device, but the current net library's behavior makes it effectively a v4 address and checks for isIpv6 fail.
- `guava-8158-036` (comment/para)  Canonically, an address like ::ffff:a.b.c.d is an IPv6 address type, not IPv4.
- `guava-8158-037` (comment/para)  What it gets used for is a different matter.
- `guava-8158-038` (comment/para)  As noted above, I don't know enough about networking to have an informed opinion, but you've got me vaguely uncomfortable with the current behavior.
- `guava-8158-039` (comment/para)  I'm not sure what it would take for me to be comfortable with actually changing the behavior, but it's a start.
- `guava-8158-040` (comment/para)  Among the various obstacles to making a change is that the current behavior does seem to be baked deeply into Java.
- `guava-8158-041` (comment/para)  [+1 code]  The only way I've found so far to force the creation of an `Inet6Address` is to pass a scope ID (or presumably `NetworkInterface`), but that results in a different value in ways that might matter:
- `guava-8158-042` (comment/para)  I suspect that we'll end up stuck the way we are now, though it's always possible that we'll learn new things that will change that.
- `guava-8158-043` (comment/para)  [+1 code]  I looked into this and found that the current behavior appears to be intentional - there's an existing test at `InetAddressesTest.java:465` that explicitly verifies mapped addresses return `Inet4Address`:
- `guava-8158-044` (comment/para)  [+1 code]  For @wdec's use case, `isMappedIPv4Address()` can detect these addresses before parsing:
- `guava-8158-045` (comment/para)  Given that (1) this matches JDK behavior, (2) normalizing is safer for ACL comparisons, and (3) a workaround exists, this seems like "working as intended" - though better documentation in the `forString()` Javadoc might help future users.
- `guava-8158-046` (comment/para)  It seems pretty clear to me that the behavior is intentional and, for better or worse, matches the way `InetAddress` chooses to handle these.
- `guava-8158-047` (comment/para)  There's a pretty long section in the class Javadoc specifically addressing this behavior.

## eclipse-vertx/vert.x#3786

- `vert.x-3786-001` (title/title)  Shared worker pool terminated after verticle undeployment
- `vert.x-3786-002` (body/para)  This applies to Vert.x 4.0.0
- `vert.x-3786-003` (body/bullet)  deploy a verticle with shared worker pool name set in `DeploymentOptions`
- `vert.x-3786-004` (body/bullet)  do some work undeploy
- `vert.x-3786-005` (body/para)  The shared worker pool name can be reused
- `vert.x-3786-006` (body/para)  The shared worker pool is terminated and remains in the shared worker map.

## eclipse-vertx/vert.x#3856

- `vert.x-3856-001` (title/title)  filesystem api: expose file locking operations
- `vert.x-3856-002` (body/para)  The `lock` and `tryLock` methods of `AsynchronousFileChannel` should be made available for `AsyncFile` wrappers, so one can perform proper file locking operations.
- `vert.x-3856-003` (comment/para)  Hi @panchmp , @vietj  is this still open for the grab ?
- `vert.x-3856-004` (comment/para)  yes it is.
- `vert.x-3856-005` (comment/para)  Hi @vietj  @tsegismont is this still available?

## eclipse-vertx/vert.x#4487

- `vert.x-4487-001` (title/title)  NPE when NetSocket.upgradeToSsl() is called if no TLS configuration in NetClientOptions
- `vert.x-4487-002` (body/para)  When there is no TLS related configuration specified in the NetClientOptions, and user tries to call `NetSocket.upgradeToSsl(handler)`, the handler will not be called because of NPE was thrown.
- `vert.x-4487-003` (body/para)  This also leads to some CI failures in other components, like:
- `vert.x-4487-004` (body/para)  The `sslProvider` in SSLHelper may be `Future.succeededFuture()` which will make `Supplier<SslContextFactory>` is null, so nothing to supply the `SslContextFactory` in this case.
- `vert.x-4487-005` (body/para)  I think we need to decide what to do in this case.
- `vert.x-4487-006` (body/para)  [+1 code]  The following test hangs and fails:
- `vert.x-4487-007` (body/para)  [+2 code]  The exception is:

## eclipse-vertx/vert.x#4660

- `vert.x-4660-001` (title/title)  WebSocket fetch and ping / pong
- `vert.x-4660-002` (body/para)  In looking at the fabric8 integration of vert.x we are using pause / fetch on websockets to control the rate at which messages are processed.
- `vert.x-4660-003` (body/para)  However it appears that ping / pong messages from the server count towards the fetch.
- `vert.x-4660-004` (body/para)  We can workaround this by not sending pings ourselves, or if we ever need to, use a pongHandler to increase the fetch.
- `vert.x-4660-005` (body/para)  [+1 code]  However if the server sends a ping since the ping handling is baked-in there's nothing we can do to increase the fetch.
- `vert.x-4660-006` (body/para)  If we remove the pause / fetch, this will complete as expected.
- `vert.x-4660-007` (body/para)  cc @vietj the current api server implementation does not send a ping, so this isn't an issue for fabric8 yet.
- `vert.x-4660-008` (body/para)  However the likely resolution of the upstream issue ⟦URL⟧ will include using ping / pong as the heartbeat mechanism for websockets, so we'll probably have to account for this eventually.
- `vert.x-4660-009` (comment/para)  Need a specific PR for 4.x
- `vert.x-4660-010` (comment/para)  #4666 should be good

## eclipse-vertx/vert.x#5748

- `vert.x-5748-001` (title/title)  NetSocket.endHandler called too early before all data is read (fires with closeHandler)
- `vert.x-5748-002` (body/para)  When using NetSocket with flow control (pause() / resume()), the endHandler is sometimes invoked too early, before all buffered data has been delivered to the read handler.
- `vert.x-5748-003` (body/para)  According to the Javadoc), the endHandler should be called after all data has been read, and possibly even after the closeHandler only if the socket is paused and there are still buffers to deliver.
- `vert.x-5748-004` (body/para)  However, in Vert.x 5.x (4.5.x is good), the endHandler is triggered at the same time as the closeHandler, effectively before all data is drained, which contradicts the documented behavior.
- `vert.x-5748-005` (body/bullet)  Create a simple TCP server that sends a large data block (e.g. ≥ 1 MB) and then closes the connection.
- `vert.x-5748-006` (body/bullet)  [+1 code]  Create a client that connects and reads with flow control
- `vert.x-5748-007` (body/bullet)  Run several times.
- `vert.x-5748-008` (body/para)  You will often see endHandler fired at the same time as closeHandler, and sometimes before the client receives all data.
- `vert.x-5748-009` (comment/para)  thanks for spotting this

## eclipse-vertx/vert.x#6006

- `vert.x-6006-001` (title/title)  Typo in the HTTP header documentation
- `vert.x-6006-002` (body/para)  Hi, sorry for writing here, I a bit confused what is current web site repo.
- `vert.x-6006-003` (body/para)  [+1 code]  Here ⟦URL⟧ as for now there is a typo, it is written
- `vert.x-6006-004` (body/para)  but actually second sentence should contain HTTP/2

## eclipse-vertx/vert.x#6276

- `vert.x-6276-001` (title/title)  Shared HTTP client incorrect reference counting
- `vert.x-6276-002` (body/para)  The shared HTTP client has a regression where closing one of its client, will close the underlying client, instead of updating the reference count and eventually closing it.

## eclipse-vertx/vert.x#6294

- `vert.x-6294-001` (title/title)  Resetting a completed HTTP/1.1 request closes a pooled connection after reuse
- `vert.x-6294-002` (body/para)  An HTTP/1.1 HttpClientRequest can retain access to its former connection after the request has completed.
- `vert.x-6294-003` (body/para)  If the connection returns to the pool and is assigned to a newer request, calling reset() on the completed request closes the physical connection now serving the newer request.
- `vert.x-6294-004` (body/para)  Calling reset() on an already completed request should be a no-op and must not affect a subsequent request using the pooled connection.
- `vert.x-6294-005` (body/para)  The subsequent request fails with io.vertx.core.http.HttpClosedException: Connection was closed.
- `vert.x-6294-006` (body/para)  Http1xClientConnection.reset() uses responses.contains(stream) || stream.responseEnded to decide that a stream is in flight. responseEnded remains true after a completed stream has left the connection tracking queues.
- `vert.x-6294-007` (body/para)  A late reset therefore marks the physical connection for closure after it has been reused.
- `vert.x-6294-008` (body/para)  The attached focused Http1xTest uses one keep-alive connection with pipelining disabled.
- `vert.x-6294-009` (body/para)  Request A completes, Request B reuses the connection, and reset() is called on A while B is active.
- `vert.x-6294-010` (body/para)  Expect: 100-continue makes the sequence deterministic; the underlying issue is not specific to 100 Continue.
- `vert.x-6294-011` (body/para)  Environment: macOS 26.5.2, OpenJDK 17.0.19.
- `vert.x-6294-012` (body/bullet)  Check out the Vert.x 4.5.31 tag.
- `vert.x-6294-013` (body/bullet)  Apply the attached test patch.
- `vert.x-6294-014` (body/bullet)  Run: mvn -Dtest=io.vertx.core.http.Http1xTest#testResetCompletedRequestDoesNotCloseReusedExpectContinueRequest test
- `vert.x-6294-015` (body/bullet)  Observe that the test fails with HttpClosedException: Connection was closed.
- `vert.x-6294-016` (body/para)  The equivalent behavior passes on the 4.2.6 code line and fails on the 4.4.1 and 4.5.31 code lines. vertx-4531-reset-completed-request-reproducer.patch.txt