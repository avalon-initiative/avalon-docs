# SDK language support

**Status:** Implemented — for the three supported languages; every other language is listed as not supported and has no planned timeline.

This is the single answer to "is there an Avalon SDK for my language?" A language is listed as supported only when there is a real, tested implementation, never on the strength of a design alone.

## Supported today

| Language | Package | Status | Notes |
| --- | --- | --- | --- |
| Rust | `avalon-sdk` in `languages/rust/`; git dependency on a release tag, or `.crate` files attached to the release. Not on crates.io. | Reference implementation | Developed alongside the server, so it is the most complete and the one the others are checked against. Provides both the integrator session and the first-party account session, and drives a software WebAuthn authenticator for registration. |
| C# | `Avalon.Sdk` in `languages/csharp/`, on the GitHub Packages NuGet feed | Supported | Targets netstandard2.1 for Unity and IL2CPP, with pure-managed Ed25519. Mirrors the Rust surface with one deliberate gap: it does not drive a WebAuthn ceremony (registration, login, add-passkey). It resumes sessions from an already-issued token and supports device login. |
| TypeScript | `@avalon-initiative/protocol-sdk` in `languages/typescript/`, on the GitHub Packages npm registry | Supported | Browser-facing, drives a real WebAuthn ceremony, and is what the Hub runs on. |

**Reference implementation** means the language the protocol is developed against first, with every other SDK checked against its behavior. **Supported** means real, tested, and safe to build on, with known gaps stated explicitly. Per-language differences are listed in [design: known limitations](design.md#known-limitations).

Packages on GitHub Packages need a token with `read:packages` even though they are public. See the [avalon-sdks README](https://github.com/avalon-initiative/avalon-sdks#readme) for install steps and the current release.

## Not supported

None of these are on a planned timeline. A language is built when a real integration needs it, not speculatively. Integrators in these languages can use the wire API directly (see [protocol API](../protocol/api.md)).

### General-purpose and backend

| Language | Typical use if built |
| --- | --- |
| Go | A server-side integration backend. |
| Python | Tooling, bots, analytics, and server-side backends. |
| C++ | Native engines without a scripting layer, including Unreal C++. |
| Java / Kotlin | A native Android client. Today: the TypeScript SDK in a WebView, or the wire API. |
| Swift | A native iOS client, the same gap as Android. |
| PHP, Ruby | Web-backend integrations. |
| Dart | Flutter clients. |
| C | A common base other native bindings could call through FFI. |

### Game-engine scripting languages

| Language | Engine | Typical use if built |
| --- | --- | --- |
| GDScript | Godot | Talking to Avalon from game code, the role C# plays for Unity. |
| Lua | Roblox (Luau), Defold, custom engines | Scripting-layer integration where Lua is the main scripting surface. |

## Related

- [SDKs overview](README.md)
- [SDK design](design.md)
- [Ecosystem: SDKs](../ecosystem/sdks.md)
