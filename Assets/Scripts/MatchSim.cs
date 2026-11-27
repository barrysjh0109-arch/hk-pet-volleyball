using UnityEngine;

// Phase 0 rally rules and movement. No Unity objects — the scene driver
// ticks this and draws the result. Not playtested in an Editor on the
// machine that generated the project.

public enum MascotId
{
    ChaCha = 0,
    Miso = 1,
    Biscuit = 2
}

public enum ShotKind
{
    Bump,
    Set,
    Spike,
    Block,
    Clear,
    Serve
}

public enum PoseKind
{
    Idle,
    Ready,
    Bump,
    Spike
}

public struct MascotDef
{
    public string displayName;
    public string blurb;
    public string spriteKey;
    public float speed;
    public float jumpV;
    public float reachX;
    public float reachY;
    public float hitRadius;
    public float visualHeight;
    public float netPad;
}

public static class Mascots
{
    public static readonly MascotDef[] All =
    {
        new MascotDef
        {
            displayName = "Cha Cha",
            blurb = "Ginger tabby. Amber eyes, small white chest blaze.",
            spriteKey = "chacha",
            speed = 7.5f,
            jumpV = 11.5f,
            reachX = 0.55f,
            reachY = 1.42f,
            hitRadius = 1.10f,
            visualHeight = 2.55f,
            netPad = 0.72f
        },
        new MascotDef
        {
            displayName = "Miso",
            blurb = "Orange-and-white. White muzzle, chest, and paws.",
            spriteKey = "miso",
            speed = 7.15f,
            jumpV = 12.05f,
            reachX = 0.52f,
            reachY = 1.36f,
            hitRadius = 1.12f,
            visualHeight = 2.48f,
            netPad = 0.74f
        },
        new MascotDef
        {
            displayName = "Biscuit",
            blurb = "Red-and-white Pembroke. Big ears, forehead blaze, white rump.",
            spriteKey = "biscuit",
            speed = 8.35f,
            jumpV = 10.4f,
            reachX = 0.78f,
            reachY = 1.02f,
            hitRadius = 1.20f,
            visualHeight = 1.95f,
            netPad = 1.28f
        }
    };
}

public static class Tune
{
    public const float CourtMin = -8.15f;
    public const float CourtMax = 8.15f;
    public const float NetH = 2.28f;
    public const float BallRadius = 0.30f;
    public const float BallGravity = -20.5f;
    public const float AthleteGravity = -34f;
    public const int SetTarget = 7;
    public const int WinBy = 2;
    public const int SetCap = 10;
    public const int MaxTouches = 3;

    public const float WorldMinX = -9.6f;
    public const float WorldMaxX = 9.6f;
    public const float WorldMinY = -1.7f;
    public const float WorldMaxY = 9.1f;
    public const float WorldW = 19.2f;
    public const float WorldH = 10.8f;
}

public struct PointResult
{
    public bool scoring;
    public int scorerSide;
    public string reason;
}

public class Athlete
{
    public int side;
    public int mascot;
    public bool ai;
    public float x;
    public float y;
    public float vy;
    public bool grounded = true;
    public float move;
    public bool jumpPressed;
    public float hitBuffer;
    public float hitLock;
    public float coyote;
    public float jumpBuffer;
    public PoseKind pose = PoseKind.Idle;
    public float poseTimer;

    public MascotDef Def => Mascots.All[mascot];
    public float Facing => -side;

    public Vector2 HitPoint => new Vector2(x + Facing * Def.reachX, y + Def.reachY);

    public void Tick(float dt)
    {
        MascotDef d = Def;
        float minX = side < 0 ? Tune.CourtMin + 0.25f : d.netPad;
        float maxX = side < 0 ? -d.netPad : Tune.CourtMax - 0.25f;
        x = Mathf.Clamp(x + move * d.speed * dt, minX, maxX);

        if (grounded) coyote = 0.09f;
        else coyote -= dt;

        if (jumpPressed) jumpBuffer = 0.11f;
        else jumpBuffer -= dt;
        jumpPressed = false;

        if (jumpBuffer > 0f && coyote > 0f)
        {
            vy = d.jumpV;
            grounded = false;
            coyote = 0f;
            jumpBuffer = 0f;
        }

        vy += Tune.AthleteGravity * dt;
        y += vy * dt;
        if (y <= 0f)
        {
            y = 0f;
            vy = 0f;
            grounded = true;
        }

        if (hitBuffer > 0f) hitBuffer -= dt;
        if (hitLock > 0f) hitLock -= dt;
        if (poseTimer > 0f) poseTimer -= dt;
    }
}

public class BallState
{
    public Vector2 pos;
    public Vector2 vel;
    public bool live;
    public int lastSide;
    public int touches;
    public bool serveLock;
    public int serverSide;
    public bool touchedNet;
    public ShotKind lastShot;
    public bool justHit;
    public string lastCall;
    public Vector2 lastCallPos;

    public void TossAbove(Athlete server)
    {
        live = false;
        serverSide = server.side;
        lastSide = 0;
        touches = 0;
        serveLock = true;
        touchedNet = false;
        justHit = false;
        float bob = Mathf.Sin(Time.time * 3.2f) * 0.1f;
        pos = new Vector2(server.x + server.Facing * 0.95f, 1.65f + bob);
        vel = Vector2.zero;
    }

    public void LaunchServe(Athlete server, float aimAbs)
    {
        live = true;
        serverSide = server.side;
        pos = new Vector2(server.x + server.Facing * 0.95f, 1.72f);
        float aimX = -server.side * aimAbs;
        vel = SolveApex(pos, aimX, 3.75f, 0.5f);
        vel = EnsureClears(pos, vel);
        vel = KeepInbound(pos, vel);
        vel = EnsureClears(pos, vel);
        CapSpeed();
        lastSide = server.side;
        touches = 1;
        serveLock = true;
        touchedNet = false;
        justHit = true;
        lastShot = ShotKind.Serve;
        lastCall = "SERVE";
        lastCallPos = pos;
    }

    public PointResult Step(float dt)
    {
        PointResult none = default;
        if (!live) return none;

        float speed = vel.magnitude;
        int n = Mathf.Clamp(Mathf.CeilToInt(speed * dt / 0.16f), 1, 10);
        float h = dt / n;
        for (int i = 0; i < n; i++)
        {
            bool landed;
            bool wentLong;
            bool hitNet;
            Integrate(ref pos, ref vel, h, out landed, out wentLong, out hitNet);
            if (hitNet) touchedNet = true;
            if (serveLock && pos.x * serverSide < -0.08f) serveLock = false;
            if (landed || wentLong)
            {
                live = false;
                vel = Vector2.zero;
                return ScoreLanding(landed && !wentLong);
            }
        }
        return none;
    }

    PointResult ScoreLanding(bool inPlayLanding)
    {
        bool inCourt = pos.x >= Tune.CourtMin && pos.x <= Tune.CourtMax;
        PointResult r = new PointResult { scoring = true };
        if (!inCourt || !inPlayLanding)
        {
            r.scorerSide = lastSide == 0 ? (pos.x < 0f ? 1 : -1) : -lastSide;
            r.reason = "Out";
            return r;
        }

        int landSide = pos.x < 0f ? -1 : 1;
        r.scorerSide = -landSide;
        if (touchedNet && lastSide == landSide) r.reason = "Net";
        else r.reason = "Point";
        return r;
    }

    public bool TryHit(Athlete a)
    {
        justHit = false;
        if (!live || a.hitLock > 0f || a.hitBuffer <= 0f) return false;
        if (serveLock && a.side == serverSide) return false;

        Vector2 hp = a.HitPoint;
        float dist = Vector2.Distance(pos, hp);
        if (dist > a.Def.hitRadius) return false;

        bool airborne = !a.grounded && (a.vy > 0.35f || a.y > 0.25f);
        bool nearNet = Mathf.Abs(a.x) < 1.85f;
        bool opponentHit = lastSide != a.side && lastSide != 0;
        bool blockWindow = airborne && nearNet && pos.y > Tune.NetH - 0.35f && opponentHit
            && Mathf.Abs(pos.x) < 1.35f && vel.x * a.side > 2.4f;

        // Don't reach through the net for a free touch.
        if (!blockWindow && pos.x * a.side < -0.2f) return false;

        int touchesNow = lastSide == a.side ? touches : 0;
        if (touchesNow >= Tune.MaxTouches)
        {
            live = false;
            vel = Vector2.zero;
            justHit = true;
            lastCall = "FOUR";
            lastCallPos = pos;
            a.hitBuffer = 0f;
            a.hitLock = 0.2f;
            // The caller reads this via a fault flag on the ball.
            faultSide = a.side;
            fault = true;
            return true;
        }

        float quality = Mathf.Clamp01(1f - Mathf.Max(0f, dist - 0.18f) / Mathf.Max(0.2f, a.Def.hitRadius - 0.18f));
        ShotKind shot;
        if (blockWindow) shot = ShotKind.Block;
        else if (airborne && pos.y > a.Def.reachY + 0.28f && (touchesNow >= 1 || pos.y > Tune.NetH + 0.05f))
            shot = ShotKind.Spike;
        else if (touchesNow >= 1 && pos.y > 1.32f && !airborne)
            shot = ShotKind.Set;
        else
            shot = ShotKind.Bump;

        if (touchesNow + 1 >= Tune.MaxTouches && shot != ShotKind.Spike && shot != ShotKind.Block)
            shot = ShotKind.Clear;

        Apply(a, shot, quality);
        lastSide = a.side;
        touches = shot == ShotKind.Block ? 0 : touchesNow + 1;
        serveLock = false;
        touchedNet = false;
        a.hitBuffer = 0f;
        a.hitLock = 0.22f;
        a.pose = (shot == ShotKind.Spike || shot == ShotKind.Block) ? PoseKind.Spike : PoseKind.Bump;
        a.poseTimer = 0.24f;
        justHit = true;
        lastShot = shot;
        lastCall = quality > 0.84f ? "PERFECT" : quality > 0.55f ? "GOOD" : "OK";
        lastCallPos = pos + new Vector2(0f, 0.45f);
        return true;
    }

    public bool fault;
    public int faultSide;

    void Apply(Athlete a, ShotKind shot, float quality)
    {
        float face = a.Facing;
        if (shot == ShotKind.Block)
        {
            float stuff = Mathf.Lerp(5.2f, -2.8f, quality);
            vel = new Vector2(face * (6.4f + quality * 3.2f), stuff);
            pos = new Vector2(face * (Tune.BallRadius + 0.1f), Mathf.Max(a.HitPoint.y, Tune.NetH + 0.08f));
            CapSpeed();
            return;
        }

        float spawnX = a.HitPoint.x;
        if (a.side < 0) spawnX = Mathf.Min(spawnX, -(Tune.BallRadius + 0.06f));
        else spawnX = Mathf.Max(spawnX, Tune.BallRadius + 0.06f);
        pos = new Vector2(spawnX, Mathf.Max(0.45f, a.HitPoint.y));

        if (shot == ShotKind.Spike)
        {
            float depth = Mathf.Lerp(0.4f, 1f, quality);
            float aimAbs = Mathf.Lerp(2.5f, 7.5f, depth);
            float front = (pos.x - a.x) * face;
            if (front < 0.02f) aimAbs = Mathf.Lerp(aimAbs, 4.3f, 0.6f);
            float aimX = -a.side * aimAbs;
            float flight = Mathf.Lerp(0.72f, 0.48f, quality);
            vel = SolveArc(pos, aimX, 0.36f, flight);
            vel = EnsureClears(pos, vel);
            vel = KeepInbound(pos, vel);
            vel = EnsureClears(pos, vel);
            CapSpeed();
            return;
        }

        if (shot == ShotKind.Clear)
        {
            float aimX = -a.side * Random.Range(3.3f, 6.5f);
            vel = SolveApex(pos, aimX, 4.35f + quality * 0.3f, 0.45f);
            vel = EnsureClears(pos, vel);
            vel = KeepInbound(pos, vel);
            vel = EnsureClears(pos, vel);
            CapSpeed();
            return;
        }

        float targetAbs = shot == ShotKind.Set ? 1.28f : 3.15f;
        float apex = shot == ShotKind.Set ? 4.95f + quality * 0.3f : 4.15f + quality * 0.4f;
        float ownX = a.side * targetAbs;
        if (shot == ShotKind.Bump && Mathf.Abs(Mathf.Abs(a.x) - targetAbs) < 0.85f)
            ownX = a.side * 2.05f;
        float arriveY = shot == ShotKind.Set ? 2.05f : 1.3f;
        vel = SolveApex(pos, ownX, apex, arriveY);
        CapSpeed();
    }

    void CapSpeed()
    {
        float m = vel.magnitude;
        if (m > 22f) vel = vel * (22f / m);
    }

    public static Vector2 SolveApex(Vector2 from, float targetX, float apex, float targetY)
    {
        float g = -Tune.BallGravity;
        apex = Mathf.Max(apex, from.y + 0.3f);
        apex = Mathf.Max(apex, targetY + 0.3f);
        float vy = Mathf.Sqrt(2f * g * (apex - from.y));
        float tUp = vy / g;
        float tDown = Mathf.Sqrt(2f * Mathf.Max(0.04f, apex - targetY) / g);
        float t = Mathf.Max(0.28f, tUp + tDown);
        float vx = (targetX - from.x) / t;
        return new Vector2(vx, vy);
    }

    public static Vector2 SolveArc(Vector2 from, float targetX, float targetY, float flight)
    {
        float t = Mathf.Max(0.3f, flight);
        float g = -Tune.BallGravity;
        float vx = (targetX - from.x) / t;
        float vy = (targetY - from.y + 0.5f * g * t * t) / t;
        return new Vector2(vx, vy);
    }

    public static Vector2 KeepInbound(Vector2 from, Vector2 vel)
    {
        float limit = Tune.CourtMax - 0.45f;
        for (int i = 0; i < 5; i++)
        {
            float x = PredictLandX(from, vel);
            if (x >= -limit && x <= limit) return vel;
            vel.x *= 0.8f;
        }
        return vel;
    }

    public static float PredictLandX(Vector2 from, Vector2 vel)
    {
        Vector2 p = from;
        Vector2 v = vel;
        for (int i = 0; i < 180; i++)
        {
            v.y += Tune.BallGravity * 0.02f;
            p += v * 0.02f;
            if (p.y <= Tune.BallRadius) return p.x;
        }
        return p.x;
    }

    public static Vector2 EnsureClears(Vector2 from, Vector2 vel)
    {
        for (int attempt = 0; attempt < 7; attempt++)
        {
            if (ClearsNet(from, vel)) return vel;
            vel.y += 1.7f;
            vel.x *= 0.94f;
        }
        return vel;
    }

    public static bool ClearsNet(Vector2 from, Vector2 vel)
    {
        Vector2 p = from;
        Vector2 v = vel;
        float prev = p.x;
        for (int i = 0; i < 90; i++)
        {
            v.y += Tune.BallGravity * 0.02f;
            p += v * 0.02f;
            if ((prev < 0f && p.x >= 0f) || (prev > 0f && p.x <= 0f))
                return p.y > Tune.NetH + Tune.BallRadius + 0.02f;
            prev = p.x;
            if (p.y < 0f) return false;
        }
        return false;
    }

    public static void Integrate(ref Vector2 pos, ref Vector2 vel, float dt, out bool landed, out bool wentLong, out bool hitNet)
    {
        landed = false;
        wentLong = false;
        hitNet = false;
        vel.y += Tune.BallGravity * dt;
        Vector2 next = pos + vel * dt;
        float x0 = pos.x;
        float x1 = next.x;
        if ((x0 < 0f && x1 > 0f) || (x0 > 0f && x1 < 0f))
        {
            float denom = x1 - x0;
            float t = denom == 0f ? 0f : (0f - x0) / denom;
            float yCross = pos.y + (next.y - pos.y) * t;
            if (yCross < Tune.NetH + Tune.BallRadius)
            {
                hitNet = true;
                float back = x0 < 0f ? -1f : 1f;
                pos = new Vector2(back * (Tune.BallRadius + 0.05f), Mathf.Max(yCross, Tune.BallRadius));
                vel.x = back * Mathf.Abs(vel.x) * 0.38f;
                vel.y = Mathf.Min(vel.y, 0.2f) - 1.6f;
                return;
            }
        }

        pos = next;
        if (Mathf.Abs(pos.x) < Tune.BallRadius * 0.9f && pos.y < Tune.NetH + Tune.BallRadius)
        {
            hitNet = true;
            float back = Mathf.Abs(x0) > 0.02f ? Mathf.Sign(x0) : (vel.x >= 0f ? -1f : 1f);
            pos.x = back * (Tune.BallRadius + 0.05f);
            vel.x = back * Mathf.Max(1.3f, Mathf.Abs(vel.x) * 0.35f);
            vel.y -= 1.3f;
        }

        if (pos.y <= Tune.BallRadius)
        {
            pos.y = Tune.BallRadius;
            landed = true;
        }

        if (pos.x < Tune.CourtMin - 1.45f || pos.x > Tune.CourtMax + 1.45f)
            wentLong = true;
    }
}

public struct BallForecast
{
    public float contactX;
    public float contactY;
    public float landingX;
    public float timeToContact;
    public float timeToLand;
    public float timeToNet;
    public bool landsOnSide;
}

public class AiBrain
{
    public float laggedX;
    public float hesitate;

    public void Think(Athlete ai, BallState ball, float dt)
    {
        if (!ball.live)
        {
            float restX = ai.side * (ai.side == ball.serverSide ? 5.4f : 4.4f);
            laggedX = Mathf.Lerp(laggedX, restX, 1f - Mathf.Exp(-8f * dt));
            ai.move = Mathf.Clamp((laggedX - ai.x) * 2.6f, -1f, 1f);
            return;
        }

        BallForecast pred = Forecast(ball, ai.side);
        int touchesNow = ball.lastSide == ai.side ? ball.touches : 0;
        bool ourSide = ball.pos.x * ai.side > 0.12f;
        bool spikeIncoming = ball.lastSide != ai.side && ball.lastSide != 0
            && ball.vel.y < -3.5f && Mathf.Abs(ball.vel.x) > 7.5f
            && Mathf.Abs(ball.pos.x) < 2.6f && ball.pos.y > Tune.NetH - 0.4f;

        float home = ai.side * 4.5f;
        float target = home;
        bool jump = false;

        if (spikeIncoming)
        {
            target = ai.side * (ai.Def.netPad + 0.15f);
            if (pred.timeToNet < 0.32f && pred.timeToNet > 0.06f) jump = true;
        }
        else if (ourSide || ball.vel.x * ai.side > 0.8f || pred.landsOnSide)
        {
            target = pred.contactX - ai.Facing * ai.Def.reachX * 0.75f;
            bool attack = touchesNow >= 1 && pred.contactY > ai.Def.reachY + 0.45f && Mathf.Abs(target) < 2.7f;
            if (touchesNow >= 2) attack = true;
            if (attack && pred.timeToContact < 0.38f && pred.timeToContact > 0.1f) jump = true;
        }

        float minX = ai.side < 0 ? Tune.CourtMin + 0.3f : ai.Def.netPad;
        float maxX = ai.side < 0 ? -ai.Def.netPad : Tune.CourtMax - 0.3f;
        target = Mathf.Clamp(target, minX, maxX);
        laggedX = Mathf.Lerp(laggedX, target, 1f - Mathf.Exp(-7.2f * dt));
        float delta = laggedX - ai.x;
        ai.move = Mathf.Abs(delta) < 0.07f ? 0f : Mathf.Clamp(delta * 2.8f, -1f, 1f);
        if (jump && ai.hitLock <= 0f) ai.jumpPressed = true;

        float dist = Vector2.Distance(ball.pos, ai.HitPoint);
        bool emergency = ourSide && ball.pos.y < 1.7f && ball.vel.y < 0f && dist < ai.Def.hitRadius * 1.25f;
        bool timed = dist < ai.Def.hitRadius * 1.12f
            || (pred.timeToContact < 0.09f + hesitate && dist < ai.Def.hitRadius * 1.45f);
        if ((timed || emergency || (spikeIncoming && dist < ai.Def.hitRadius * 1.3f)) && ai.hitLock <= 0f)
            ai.hitBuffer = Mathf.Max(ai.hitBuffer, 0.1f);
    }

    public static BallForecast Forecast(BallState ball, int side)
    {
        BallForecast f = new BallForecast
        {
            timeToContact = 9f,
            timeToLand = 9f,
            timeToNet = 9f,
            contactX = side * 4.2f,
            contactY = 1.1f
        };
        Vector2 p = ball.pos;
        Vector2 v = ball.vel;
        bool found = false;
        float t = 0f;
        for (int i = 0; i < 170; i++)
        {
            float prev = p.x;
            bool landed;
            bool wentLong;
            bool hitNet;
            BallState.Integrate(ref p, ref v, 0.02f, out landed, out wentLong, out hitNet);
            t += 0.02f;
            if (f.timeToNet > 8f && ((prev < 0f && p.x >= 0f) || (prev > 0f && p.x <= 0f)))
                f.timeToNet = t;
            bool ourSide = p.x * side > 0.1f;
            if (!found && ourSide && v.y < 0.5f && p.y < 2.6f && p.y > 0.35f)
            {
                found = true;
                f.timeToContact = t;
                f.contactX = p.x;
                f.contactY = p.y;
            }
            if (landed || wentLong)
            {
                f.timeToLand = t;
                f.landingX = p.x;
                f.landsOnSide = p.x * side > 0f && p.x >= Tune.CourtMin && p.x <= Tune.CourtMax;
                if (!found)
                {
                    f.contactX = Mathf.Clamp(p.x, Tune.CourtMin, Tune.CourtMax);
                    f.contactY = 0.7f;
                    f.timeToContact = t;
                    f.landsOnSide = f.landsOnSide || (p.x * side > 0f);
                }
                break;
            }
        }
        return f;
    }
}

public static class SetRules
{
    public static bool IsOver(int a, int b)
    {
        int hi = Mathf.Max(a, b);
        int lo = Mathf.Min(a, b);
        if (hi >= Tune.SetCap) return true;
        return hi >= Tune.SetTarget && hi - lo >= Tune.WinBy;
    }
}
