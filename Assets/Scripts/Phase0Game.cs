using System.Collections.Generic;
using UnityEngine;

// Harbour Rooftop — Phase 0. Press Play, pick a mascot, play a short set
// versus the AI. This file was not run in Play Mode (no Unity Editor on
// the machine that wrote it).

[DefaultExecutionOrder(-50)]
public class Phase0Game : MonoBehaviour
{
    enum Mode
    {
        Select,
        Serve,
        Rally,
        Point,
        Done
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void AutoBoot()
    {
        if (UnityEngine.Object.FindAnyObjectByType<Phase0Game>() != null) return;
        GameObject go = new GameObject("Phase0");
        go.AddComponent<Phase0Game>();
    }

    Mode mode = Mode.Select;
    int playerMascot;
    int aiMascot = 1;
    int spectatorMascot = 2;
    int scoreL;
    int scoreR;
    int serverSide = -1;
    float timer;
    string banner = "";
    string bannerSub = "";

    Athlete player = new Athlete();
    Athlete cpu = new Athlete();
    BallState ball = new BallState();
    AiBrain brain = new AiBrain();

    Camera cam;
    Vector3 camBase;
    float shake;

    SpriteRenderer backdropSr;
    SpriteRenderer netSr;
    SpriteRenderer ballSr;
    SpriteRenderer markerSr;
    SpriteRenderer flashSr;
    SpriteRenderer[] trail;
    ActorView playerView;
    ActorView cpuView;
    ActorView specView;
    Sprite shadowSprite;
    Sprite flashSprite;

    Sprite[,,] poses; // [mascot, pose]
    AudioSource audioSrc;
    AudioClip sndBump, sndSet, sndSpike, sndBlock, sndServe, sndPoint, sndUi;
    Font font;
    float flashLife;
    float ballPunch;
    bool serveArmed;
    readonly List<Floater> floaters = new List<Floater>();
    bool artMissing;

    struct Floater
    {
        public Vector3 world;
        public string text;
        public float life;
        public Color color;
    }

    class ActorView
    {
        public SpriteRenderer body;
        public SpriteRenderer shadow;
    }

    void Awake()
    {
        Time.timeScale = 1f;
        Application.targetFrameRate = 60;
        font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        if (font == null) font = Resources.GetBuiltinResource<Font>("Arial.ttf");
        EnsureCamera();
        LoadArt();
        BuildWorld();
        MakeAudio();
        ResetAthletes(-4.4f, 4.8f);
    }

    void EnsureCamera()
    {
        cam = Camera.main;
        if (cam == null)
        {
            GameObject go = new GameObject("Main Camera");
            go.tag = "MainCamera";
            cam = go.AddComponent<Camera>();
            go.AddComponent<AudioListener>();
        }
        else if (cam.GetComponent<AudioListener>() == null)
        {
            cam.gameObject.AddComponent<AudioListener>();
        }

        cam.orthographic = true;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.55f, 0.74f, 0.82f);
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 40f;
        FitCamera();
    }

    void FitCamera()
    {
        if (cam == null) return;
        float aspect = cam.aspect > 0.2f ? cam.aspect : 16f / 9f;
        float halfH = Mathf.Max(5.35f, 9.45f / aspect);
        cam.orthographicSize = halfH;
        camBase = new Vector3(0f, 3.05f, -10f);
        if (shake <= 0f) cam.transform.position = camBase;
    }

    void LoadArt()
    {
        poses = new Sprite[3, 4];
        string[] poseNames = { "idle", "ready", "bump", "spike" };
        for (int m = 0; m < 3; m++)
        {
            string key = Mascots.All[m].spriteKey;
            for (int p = 0; p < 4; p++)
            {
                poses[m, p] = Resources.Load<Sprite>("Athletes/" + key + "_" + poseNames[p]);
                if (poses[m, p] == null)
                {
                    artMissing = true;
                    poses[m, p] = PlaceholderMascot(m);
                }
            }
        }
        if (artMissing)
            Debug.LogWarning("HK Pet Volleyball: one or more athlete sprites failed to import. Placeholders are in use. Check the sprite import settings on Assets/Resources/Athletes.");
    }

    Sprite LoadOrFallback(string path, Color color, int size, float pivotY)
    {
        Sprite s = Resources.Load<Sprite>(path);
        if (s != null) return s;
        artMissing = true;
        Texture2D tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
        Color[] pix = new Color[size * size];
        float r = size * 0.45f;
        Vector2 c = new Vector2(size * 0.5f, size * 0.5f);
        for (int y = 0; y < size; y++)
        for (int x = 0; x < size; x++)
        {
            float d = Vector2.Distance(new Vector2(x, y), c);
            pix[y * size + x] = d < r ? color : Color.clear;
        }
        tex.SetPixels(pix);
        tex.Apply();
        tex.filterMode = FilterMode.Bilinear;
        return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, pivotY), 100f);
    }

    void BuildWorld()
    {
        shadowSprite = MakeEllipseSprite(128, 64, new Color(0f, 0f, 0f, 0.45f));
        flashSprite = MakeRingSprite();

        Sprite backdrop = LoadOrFallback("Court/backdrop", new Color(0.55f, 0.75f, 0.85f), 32, 0.5f);
        backdropSr = MakeSr("Backdrop", backdrop, 0);
        FitCenter(backdropSr.transform, backdrop, new Vector2(Tune.WorldW, Tune.WorldH), new Vector2(0f, (Tune.WorldMinY + Tune.WorldMaxY) * 0.5f));

        Sprite net = LoadOrFallback("Court/net", new Color(0.95f, 0.95f, 0.95f), 32, 0f);
        netSr = MakeSr("Net", net, 8);
        FitBottom(netSr.transform, net, Tune.NetH + 0.18f, 0f, 0f, 1f);

        Sprite ballSprite = LoadOrFallback("Court/ball", new Color(0.95f, 0.55f, 0.25f), 64, 0.5f);
        ballSr = MakeSr("Ball", ballSprite, 18);
        FitCenter(ballSr.transform, ballSprite, new Vector2(Tune.BallRadius * 2f, Tune.BallRadius * 2f), Vector2.zero);

        markerSr = MakeSr("Landing", shadowSprite, 6);
        markerSr.color = new Color(1f, 0.82f, 0.35f, 0.85f);
        markerSr.transform.localScale = new Vector3(0.7f, 0.22f, 1f);

        flashSr = MakeSr("Flash", flashSprite, 20);
        flashSr.enabled = false;

        trail = new SpriteRenderer[7];
        for (int i = 0; i < trail.Length; i++)
        {
            trail[i] = MakeSr("Trail" + i, ballSprite, 16);
            trail[i].color = new Color(1f, 1f, 1f, 0f);
        }

        playerView = MakeActor("Player");
        cpuView = MakeActor("Cpu");
        specView = MakeActor("Spectator");
    }

    ActorView MakeActor(string name)
    {
        ActorView v = new ActorView();
        v.shadow = MakeSr(name + "Shadow", shadowSprite, 2);
        v.body = MakeSr(name, PlaceholderMascot(0), 12);
        return v;
    }

    Sprite PlaceholderMascot(int mascot)
    {
        Color c = mascot == 2 ? new Color(0.83f, 0.45f, 0.22f) : new Color(0.88f, 0.52f, 0.22f);
        return LoadOrFallback("Athletes/" + Mascots.All[mascot].spriteKey + "_idle", c, 64, 0f);
    }

    SpriteRenderer MakeSr(string name, Sprite sprite, int order)
    {
        GameObject go = new GameObject(name);
        go.transform.SetParent(transform, false);
        SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.sortingOrder = order;
        return sr;
    }

    static void FitCenter(Transform t, Sprite s, Vector2 worldSize, Vector2 worldCenter)
    {
        Bounds b = s.bounds;
        float sx = worldSize.x / Mathf.Max(0.001f, b.size.x);
        float sy = worldSize.y / Mathf.Max(0.001f, b.size.y);
        t.localScale = new Vector3(sx, sy, 1f);
        t.position = new Vector3(
            worldCenter.x - b.center.x * sx,
            worldCenter.y - b.center.y * sy,
            0f);
    }

    static void FitBottom(Transform t, Sprite s, float worldHeight, float worldCenterX, float floorY, float facingSign)
    {
        Bounds b = s.bounds;
        float scale = worldHeight / Mathf.Max(0.001f, b.size.y);
        float sx = scale * facingSign;
        t.localScale = new Vector3(sx, scale, 1f);
        t.position = new Vector3(
            worldCenterX - b.center.x * sx,
            floorY - b.min.y * scale,
            0f);
    }

    Sprite MakeEllipseSprite(int w, int h, Color color)
    {
        Texture2D tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        Color[] pix = new Color[w * h];
        for (int y = 0; y < h; y++)
        for (int x = 0; x < w; x++)
        {
            float nx = (x - w * 0.5f) / (w * 0.5f);
            float ny = (y - h * 0.5f) / (h * 0.5f);
            float d = nx * nx + ny * ny;
            float a = Mathf.Clamp01(1f - d);
            a = a * a;
            Color c = color;
            c.a *= a;
            pix[y * w + x] = c;
        }
        tex.SetPixels(pix);
        tex.Apply();
        tex.filterMode = FilterMode.Bilinear;
        return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f);
    }

    Sprite MakeRingSprite()
    {
        int n = 128;
        Texture2D tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
        Color[] pix = new Color[n * n];
        Vector2 c = new Vector2(n * 0.5f, n * 0.5f);
        for (int y = 0; y < n; y++)
        for (int x = 0; x < n; x++)
        {
            float d = Vector2.Distance(new Vector2(x, y), c) / (n * 0.5f);
            float a = Mathf.Clamp01(1f - Mathf.Abs(d - 0.72f) * 8f);
            pix[y * n + x] = new Color(1f, 0.95f, 0.85f, a);
        }
        tex.SetPixels(pix);
        tex.Apply();
        return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 100f);
    }

    void MakeAudio()
    {
        audioSrc = gameObject.AddComponent<AudioSource>();
        audioSrc.playOnAwake = false;
        audioSrc.spatialBlend = 0f;
        sndBump = Tone("bump", 210f, 0.09f, 16f, false);
        sndSet = Tone("set", 480f, 0.11f, 12f, false);
        sndSpike = Tone("spike", 130f, 0.13f, 18f, true);
        sndBlock = Tone("block", 170f, 0.08f, 20f, true);
        sndServe = Tone("serve", 320f, 0.1f, 14f, false);
        sndPoint = Tone("point", 740f, 0.22f, 6f, false);
        sndUi = Tone("ui", 620f, 0.05f, 22f, false);
    }

    static AudioClip Tone(string name, float freq, float dur, float decay, bool noise)
    {
        int rate = 44100;
        int n = Mathf.Max(1, (int)(rate * dur));
        float[] data = new float[n];
        float seed = freq;
        for (int i = 0; i < n; i++)
        {
            float t = i / (float)rate;
            float env = Mathf.Exp(-decay * t);
            float s = Mathf.Sin(2f * Mathf.PI * freq * t);
            if (noise)
            {
                seed = (seed * 17.13f + 4.7f) % 1f;
                s = s * 0.45f + (seed * 2f - 1f) * 0.55f;
            }
            data[i] = s * env * 0.32f;
        }
        AudioClip clip = AudioClip.Create(name, n, 1, rate, false);
        clip.SetData(data, 0);
        return clip;
    }

    void Play(AudioClip clip, float vol)
    {
        if (clip != null && audioSrc != null) audioSrc.PlayOneShot(clip, vol);
    }

    void ResetAthletes(float px, float cx)
    {
        player.side = -1;
        player.mascot = playerMascot;
        player.ai = false;
        player.x = px;
        player.y = 0f;
        player.vy = 0f;
        player.grounded = true;
        player.hitBuffer = 0f;
        player.hitLock = 0f;
        player.move = 0f;
        player.poseTimer = 0f;

        cpu.side = 1;
        cpu.mascot = aiMascot;
        cpu.ai = true;
        cpu.x = cx;
        cpu.y = 0f;
        cpu.vy = 0f;
        cpu.grounded = true;
        cpu.hitBuffer = 0f;
        cpu.hitLock = 0f;
        cpu.move = 0f;
        cpu.poseTimer = 0f;
        brain.laggedX = cx;
        brain.hesitate = 0f;
        ball.fault = false;
    }

    void BeginServe()
    {
        mode = Mode.Serve;
        timer = 0f;
        serveArmed = false;
        ball.fault = false;
        player.hitBuffer = 0f;
        cpu.hitBuffer = 0f;
        Athlete server = serverSide < 0 ? player : cpu;
        banner = serverSide < 0 ? "Your serve" : "AI serve";
        bannerSub = "Hit to send it over";
    }

    void StartMatch(int mascot)
    {
        playerMascot = Mathf.Clamp(mascot, 0, 2);
        int roll = Random.Range(0, 2);
        aiMascot = (playerMascot + 1 + roll) % 3;
        spectatorMascot = 3 - playerMascot - aiMascot;
        scoreL = 0;
        scoreR = 0;
        serverSide = -1;
        ResetAthletes(-4.6f, 5.0f);
        Play(sndUi, 0.5f);
        BeginServe();
        banner = Mascots.All[playerMascot].displayName + "  vs  " + Mascots.All[aiMascot].displayName;
        bannerSub = "First to 7, win by 2, cap 10";
        timer = -0.4f;
    }

    void Update()
    {
        float dt = Mathf.Min(Time.deltaTime, 0.033f);
        FitCamera();
        if (mode == Mode.Select)
        {
            if (Input.GetKeyDown(KeyCode.Alpha1) || Input.GetKeyDown(KeyCode.Keypad1)) StartMatch(0);
            else if (Input.GetKeyDown(KeyCode.Alpha2) || Input.GetKeyDown(KeyCode.Keypad2)) StartMatch(1);
            else if (Input.GetKeyDown(KeyCode.Alpha3) || Input.GetKeyDown(KeyCode.Keypad3)) StartMatch(2);
        }
        else if (mode == Mode.Done)
        {
            if (Input.GetKeyDown(KeyCode.R)) Rematch();
            if (Input.GetKeyDown(KeyCode.M) || Input.GetKeyDown(KeyCode.Escape)) mode = Mode.Select;
        }
        else
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                mode = Mode.Select;
                Play(sndUi, 0.4f);
            }
            else
            {
                ReadPlayerInput();
                TickMatch(dt);
            }
        }

        Present(dt);
        shake = Mathf.MoveTowards(shake, 0f, dt * 1.6f);
        if (cam != null)
        {
            float jx = shake > 0f ? Mathf.Sin(Time.time * 73f) * shake : 0f;
            float jy = shake > 0f ? Mathf.Cos(Time.time * 61f) * shake : 0f;
            cam.transform.position = camBase + new Vector3(jx, jy, 0f);
        }
    }

    void ReadPlayerInput()
    {
        if (mode == Mode.Point) return;
        float move = 0f;
        if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) move -= 1f;
        if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) move += 1f;
        player.move = move;
        if (Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow) || Input.GetKeyDown(KeyCode.Space))
            player.jumpPressed = true;
        if (mode == Mode.Serve && serverSide < 0 && HitPressed())
            serveArmed = true;
        else if (player.hitLock <= 0f && HitPressed())
            player.hitBuffer = 0.16f;
    }

    static bool HitPressed()
    {
        return Input.GetKeyDown(KeyCode.F)
            || Input.GetKeyDown(KeyCode.J)
            || Input.GetKeyDown(KeyCode.K)
            || Input.GetKeyDown(KeyCode.S)
            || Input.GetKeyDown(KeyCode.DownArrow);
    }

    void TickMatch(float dt)
    {
        if (mode == Mode.Serve)
        {
            timer += dt;
            Athlete server = serverSide < 0 ? player : cpu;
            ball.TossAbove(server);
            brain.Think(cpu, ball, dt);
            player.Tick(dt);
            cpu.Tick(dt);
            bool launch = false;
            float aim = Random.Range(3.8f, 6.3f);
            if (serverSide < 0 && serveArmed && timer > 0.2f)
            {
                launch = true;
                serveArmed = false;
                player.hitBuffer = 0f;
            }
            else if (serverSide > 0 && timer > 0.95f)
            {
                launch = true;
                aim = Random.Range(3.5f, 6.4f);
            }
            if (launch)
            {
                ball.LaunchServe(server, aim);
                server.pose = PoseKind.Bump;
                server.poseTimer = 0.2f;
                server.hitBuffer = 0f;
                server.hitLock = 0.25f;
                brain.hesitate = Random.value < 0.16f ? 0.08f : 0f;
                Play(sndServe, 0.55f);
                mode = Mode.Rally;
                banner = "";
                bannerSub = "";
            }
            return;
        }

        if (mode == Mode.Point)
        {
            timer -= dt;
            player.move = 0f;
            cpu.move = 0f;
            player.Tick(dt);
            cpu.Tick(dt);
            if (timer <= 0f)
            {
                if (SetRules.IsOver(scoreL, scoreR)) mode = Mode.Done;
                else
                {
                    serverSide = -serverSide;
                    ResetAthletes(player.x, cpu.x);
                    BeginServe();
                }
            }
            return;
        }

        // Rally.
        brain.Think(cpu, ball, dt);
        ball.fault = false;
        ball.justHit = false;
        bool playerHit = ball.TryHit(player);
        if (!ball.fault && !playerHit) ball.TryHit(cpu);
        NoteHit();
        if (ball.fault)
        {
            Award(-ball.faultSide, "Four touches");
            return;
        }

        PointResult point = ball.Step(dt);
        player.Tick(dt);
        cpu.Tick(dt);
        if (point.scoring) Award(point.scorerSide, point.reason);
    }

    void NoteHit()
    {
        if (!ball.justHit || ball.fault) return;
        switch (ball.lastShot)
        {
            case ShotKind.Spike:
                Play(sndSpike, 0.7f);
                shake = Mathf.Max(shake, 0.09f);
                ballPunch = 0.28f;
                break;
            case ShotKind.Block:
                Play(sndBlock, 0.65f);
                shake = Mathf.Max(shake, 0.07f);
                ballPunch = 0.2f;
                break;
            case ShotKind.Set:
                Play(sndSet, 0.55f);
                ballPunch = 0.16f;
                break;
            case ShotKind.Serve:
                ballPunch = 0.12f;
                break;
            default:
                Play(sndBump, 0.6f);
                ballPunch = 0.18f;
                break;
        }
        flashLife = 0.14f;
        Color col = ball.lastCall == "PERFECT" ? new Color(1f, 0.82f, 0.25f) : new Color(1f, 0.97f, 0.9f);
        floaters.Add(new Floater { world = ball.lastCallPos, text = ball.lastCall, life = 0.7f, color = col });
        if (ball.lastSide == player.side)
            brain.hesitate = Random.value < 0.18f ? 0.09f : 0f;
    }

    void Award(int scorerSide, string reason)
    {
        if (scorerSide < 0) scoreL++;
        else scoreR++;
        string who = scorerSide < 0 ? Mascots.All[playerMascot].displayName : Mascots.All[aiMascot].displayName;
        banner = who + " scores";
        bannerSub = reason;
        mode = Mode.Point;
        timer = 1.15f;
        Play(sndPoint, 0.5f);
        shake = Mathf.Max(shake, 0.05f);
        ball.live = false;
    }

    void Rematch()
    {
        scoreL = 0;
        scoreR = 0;
        serverSide = -1;
        ResetAthletes(-4.6f, 5.0f);
        Play(sndUi, 0.45f);
        BeginServe();
    }

    void Present(float dt)
    {
        if (mode == Mode.Select)
        {
            playerView.body.enabled = false;
            playerView.shadow.enabled = false;
            cpuView.body.enabled = false;
            cpuView.shadow.enabled = false;
            specView.body.enabled = false;
            specView.shadow.enabled = false;
            ballSr.enabled = false;
            markerSr.enabled = false;
            flashSr.enabled = false;
            for (int i = 0; i < trail.Length; i++) trail[i].enabled = false;
            return;
        }

        for (int i = 0; i < trail.Length; i++) trail[i].enabled = true;
        playerView.body.enabled = true;
        cpuView.body.enabled = true;
        PoseOn(playerView, player, 1f);
        PoseOn(cpuView, cpu, 1f);
        PoseSpectator();

        bool showBall = mode != Mode.Select && mode != Mode.Done || ball.live;
        showBall = mode != Mode.Select;
        ballSr.enabled = showBall;
        if (showBall)
        {
            ballPunch = Mathf.MoveTowards(ballPunch, 0f, dt * 1.8f);
            float punch = 1f + ballPunch;
            Vector2 size = new Vector2(Tune.BallRadius * 2f * punch, Tune.BallRadius * 2f * (1f - ballPunch * 0.35f));
            Sprite s = ballSr.sprite;
            if (s != null)
            {
                Bounds b = s.bounds;
                float sx = size.x / Mathf.Max(0.001f, b.size.x);
                float sy = size.y / Mathf.Max(0.001f, b.size.y);
                ballSr.transform.localScale = new Vector3(sx, sy, 1f);
                ballSr.transform.position = new Vector3(
                    ball.pos.x - b.center.x * sx,
                    ball.pos.y - b.center.y * sy,
                    0f);
            }
            else ballSr.transform.position = ball.pos;
            ballSr.transform.Rotate(0f, 0f, -ball.vel.x * dt * 40f);

            Vector3 prev = ballSr.transform.position;
            for (int i = trail.Length - 1; i >= 0; i--)
            {
                Vector3 p = i == 0 ? prev : trail[i - 1].transform.position;
                // Shift history once per frame by copying previous positions after placing the ball.
            }
            for (int i = trail.Length - 1; i >= 1; i--)
                trail[i].transform.position = trail[i - 1].transform.position;
            trail[0].transform.position = ballSr.transform.position;
            for (int i = 0; i < trail.Length; i++)
            {
                float a = ball.live ? 0.22f * (1f - i / (float)trail.Length) : 0f;
                trail[i].color = new Color(1f, 0.95f, 0.85f, a);
                float sc = 0.55f - i * 0.05f;
                trail[i].transform.localScale = ballSr.transform.localScale * sc;
            }
        }
        else
        {
            for (int i = 0; i < trail.Length; i++) trail[i].color = new Color(1f, 1f, 1f, 0f);
        }

        markerSr.enabled = mode == Mode.Rally && ball.live && ball.vel.y < -0.5f;
        if (markerSr.enabled)
        {
            BallForecast f = AiBrain.Forecast(ball, ball.vel.x >= 0f ? 1 : -1);
            float x = f.landingX;
            bool inbound = x >= Tune.CourtMin && x <= Tune.CourtMax && f.timeToLand < 4f;
            markerSr.enabled = inbound;
            markerSr.transform.position = new Vector3(x, 0.04f, 0f);
        }

        flashLife -= dt;
        flashSr.enabled = flashLife > 0f && mode != Mode.Select;
        if (flashSr.enabled)
        {
            float u = 1f - flashLife / 0.14f;
            flashSr.transform.position = ball.pos;
            flashSr.transform.localScale = Vector3.one * Mathf.Lerp(0.4f, 1.8f, u);
            flashSr.color = new Color(1f, 0.95f, 0.8f, 1f - u);
        }

        for (int i = floaters.Count - 1; i >= 0; i--)
        {
            Floater f = floaters[i];
            f.life -= dt;
            f.world.y += dt * 0.8f;
            if (f.life <= 0f) floaters.RemoveAt(i);
            else floaters[i] = f;
        }
    }

    void PoseOn(ActorView view, Athlete a, float heightScale)
    {
        PoseKind pose = a.poseTimer > 0f ? a.pose : ChoosePose(a);
        Sprite sprite = SpriteFor(a.mascot, pose);
        if (sprite == null) return;
        view.body.sprite = sprite;
        float h = Mascots.All[a.mascot].visualHeight * heightScale;
        float squash = 1f;
        if (a.grounded && a.vy == 0f && a.poseTimer > 0.12f && a.pose == PoseKind.Bump) squash = 0.92f;
        Bounds b = sprite.bounds;
        float scale = h / Mathf.Max(0.001f, b.size.y);
        float sx = scale * a.Facing;
        float sy = scale * squash;
        view.body.transform.localScale = new Vector3(sx, sy, 1f);
        float bob = a.grounded ? Mathf.Sin(Time.time * 5.5f + a.side * 2f) * 0.025f : 0f;
        float floor = a.y + bob;
        view.body.transform.position = new Vector3(
            a.x - b.center.x * sx,
            floor - b.min.y * sy,
            0f);
        view.shadow.enabled = true;
        float lift = Mathf.Clamp01(a.y / 2.2f);
        view.shadow.transform.position = new Vector3(a.x, 0.03f, 0f);
        view.shadow.transform.localScale = new Vector3(0.95f + (1f - lift) * 0.3f, 0.28f, 1f) * (a.mascot == 2 ? 1.25f : 1f);
        view.shadow.color = new Color(0f, 0f, 0f, 0.35f * (1f - lift));
    }

    void PoseSpectator()
    {
        Sprite sprite = SpriteFor(spectatorMascot, PoseKind.Idle);
        if (sprite == null || mode == Mode.Select)
        {
            specView.body.enabled = false;
            specView.shadow.enabled = false;
            return;
        }
        specView.body.enabled = true;
        specView.shadow.enabled = false;
        specView.body.sprite = sprite;
        specView.body.color = new Color(1f, 1f, 1f, 0.95f);
        float h = Mascots.All[spectatorMascot].visualHeight * 0.62f;
        Bounds b = sprite.bounds;
        float scale = h / Mathf.Max(0.001f, b.size.y);
        float bob = Mathf.Sin(Time.time * 2.4f) * 0.03f;
        float floor = 1.12f + bob;
        float x = -7.15f;
        specView.body.transform.localScale = new Vector3(scale, scale, 1f);
        specView.body.transform.position = new Vector3(
            x - b.center.x * scale,
            floor - b.min.y * scale,
            0f);
        specView.body.sortingOrder = 4;
    }

    PoseKind ChoosePose(Athlete a)
    {
        if (!a.grounded) return PoseKind.Spike;
        bool ballHere = ball.live && ball.pos.x * a.side > -0.2f;
        if (Mathf.Abs(a.move) > 0.15f || ballHere) return PoseKind.Ready;
        return PoseKind.Idle;
    }

    Sprite SpriteFor(int mascot, PoseKind pose)
    {
        int p = (int)pose;
        if (poses != null && poses[mascot, p] != null) return poses[mascot, p];
        if (poses != null && poses[mascot, 0] != null) return poses[mascot, 0];
        return null;
    }

    void OnGUI()
    {
        if (mode == Mode.Select) DrawSelect();
        else DrawHud();
        DrawFloaters();
    }

    void DrawSelect()
    {
        float w = Screen.width;
        float h = Screen.height;
        GUI.color = new Color(0.08f, 0.1f, 0.14f, 0.55f);
        GUI.DrawTexture(new Rect(0, 0, w, h), Texture2D.whiteTexture);
        GUI.color = Color.white;

        GUIStyle title = Style(Mathf.RoundToInt(Mathf.Min(54f, w * 0.04f)), new Color(1f, 0.95f, 0.88f), TextAnchor.UpperCenter);
        GUIStyle sub = Style(Mathf.RoundToInt(Mathf.Min(22f, w * 0.018f)), new Color(0.75f, 0.9f, 0.88f), TextAnchor.UpperCenter);
        GUI.Label(new Rect(0, h * 0.05f, w, 64), "海旁排球", title);
        GUI.Label(new Rect(0, h * 0.05f + 58, w, 36), "HK PET VOLLEYBALL  ·  HARBOUR ROOFTOP", sub);
        GUI.Label(new Rect(0, h * 0.05f + 92, w, 30), "Pick a mascot. The other two take the far side and the railing.", sub);

        float colW = Mathf.Min(300f, (w - 80f) / 3f);
        float gap = 24f;
        float total = colW * 3f + gap * 2f;
        float x0 = (w - total) * 0.5f;
        float y0 = h * 0.28f;
        int shown = ((int)(Time.time * 1.3f)) % 4;
        string[] keys = { "1", "2", "3" };
        for (int i = 0; i < 3; i++)
        {
            Rect card = new Rect(x0 + i * (colW + gap), y0, colW, h * 0.48f);
            GUI.color = new Color(1f, 0.97f, 0.92f, 0.94f);
            GUI.DrawTexture(card, Texture2D.whiteTexture);
            GUI.color = Color.white;
            Sprite sp = SpriteFor(i, (PoseKind)shown);
            if (sp != null)
            {
                float side = Mathf.Min(card.width - 24f, card.height * 0.48f);
                DrawSprite(new Rect(card.x + (card.width - side) * 0.5f, card.y + 12f, side, side), sp);
            }
            GUIStyle name = Style(26, new Color(0.25f, 0.14f, 0.1f), TextAnchor.UpperCenter);
            GUIStyle blurb = Style(15, new Color(0.35f, 0.24f, 0.18f), TextAnchor.UpperCenter);
            blurb.wordWrap = true;
            blurb.fontStyle = FontStyle.Normal;
            GUI.Label(new Rect(card.x + 8, card.yMax - 132, card.width - 16, 32), Mascots.All[i].displayName, name);
            GUI.Label(new Rect(card.x + 10, card.yMax - 98, card.width - 20, 52), Mascots.All[i].blurb, blurb);
            GUI.backgroundColor = new Color(0.9f, 0.42f, 0.28f);
            if (GUI.Button(new Rect(card.x + 18, card.yMax - 42, card.width - 36, 32), "Play  [" + keys[i] + "]"))
                StartMatch(i);
            GUI.backgroundColor = Color.white;
        }

        GUIStyle hint = Style(16, new Color(1f, 0.95f, 0.88f), TextAnchor.UpperCenter);
        hint.fontStyle = FontStyle.Normal;
        GUI.Label(new Rect(40, h - 78, w - 80, 64),
            "Move  A/D or arrows     Jump  W / Up / Space     Hit  F / J / K / S / Down\n" +
            "Low hit bumps. High grounded hit sets. Jump and hit to spike. Jump at the net to block.\n" +
            "Click the Game view once so the keyboard reaches the match.",
            hint);
    }

    void DrawHud()
    {
        float w = Screen.width;
        GUIStyle score = Style(54, Color.white, TextAnchor.UpperCenter);
        GUIStyle name = Style(18, new Color(1f, 0.95f, 0.86f), TextAnchor.UpperCenter);
        GUIStyle small = Style(16, new Color(1f, 0.95f, 0.88f), TextAnchor.UpperCenter);
        small.fontStyle = FontStyle.Normal;
        GUIStyle big = Style(40, new Color(1f, 0.95f, 0.86f), TextAnchor.MiddleCenter);

        string leftName = Mascots.All[playerMascot].displayName;
        string rightName = Mascots.All[aiMascot].displayName;
        GUI.Label(new Rect(w * 0.5f - 220, 12, 160, 64), scoreL.ToString(), score);
        GUI.Label(new Rect(w * 0.5f + 60, 12, 160, 64), scoreR.ToString(), score);
        GUI.Label(new Rect(w * 0.5f - 40, 28, 80, 40), "–", score);
        GUI.Label(new Rect(w * 0.5f - 220, 70, 160, 24), leftName, name);
        GUI.Label(new Rect(w * 0.5f + 60, 70, 160, 24), rightName, name);
        DrawPips(w * 0.5f - 150, 96, -1);
        DrawPips(w * 0.5f + 130, 96, 1);

        if (!string.IsNullOrEmpty(banner))
        {
            GUI.Label(new Rect(0, Screen.height * 0.2f, w, 56), banner, big);
            GUI.Label(new Rect(0, Screen.height * 0.2f + 52, w, 28), bannerSub, small);
        }

        if (mode == Mode.Serve && serverSide < 0)
            GUI.Label(new Rect(0, Screen.height * 0.72f, w, 32), "Press F to serve", big);

        GUI.Label(new Rect(0, Screen.height - 36, w, 28),
            "A/D move    Space jump    F hit    Esc mascots    First to 7, win by 2, cap 10",
            small);

        if (mode == Mode.Done)
        {
            GUI.color = new Color(0.08f, 0.1f, 0.14f, 0.62f);
            GUI.DrawTexture(new Rect(0, 0, w, Screen.height), Texture2D.whiteTexture);
            GUI.color = Color.white;
            bool you = scoreL > scoreR;
            string winner = you ? leftName : rightName;
            GUI.Label(new Rect(0, Screen.height * 0.32f, w, 60), winner + " takes the set", big);
            GUI.Label(new Rect(0, Screen.height * 0.32f + 64, w, 50), scoreL + "  –  " + scoreR, score);
            GUI.backgroundColor = new Color(0.9f, 0.42f, 0.28f);
            float bw = 220f;
            if (GUI.Button(new Rect(w * 0.5f - bw - 10, Screen.height * 0.55f, bw, 42), "Rematch  [R]")) Rematch();
            GUI.backgroundColor = new Color(0.95f, 0.9f, 0.82f);
            if (GUI.Button(new Rect(w * 0.5f + 10, Screen.height * 0.55f, bw, 42), "Change mascot  [M]"))
                mode = Mode.Select;
            GUI.backgroundColor = Color.white;
        }
        else
        {
            GUI.backgroundColor = new Color(1f, 1f, 1f, 0.7f);
            if (GUI.Button(new Rect(12, 12, 130, 26), "Mascots"))
                mode = Mode.Select;
            GUI.backgroundColor = Color.white;
        }
    }

    void DrawPips(float x, float y, int side)
    {
        int n = 0;
        if (ball.live && ball.lastSide == side) n = Mathf.Clamp(ball.touches, 0, 3);
        for (int i = 0; i < 3; i++)
        {
            GUI.color = i < n ? new Color(1f, 0.78f, 0.3f) : new Color(1f, 1f, 1f, 0.35f);
            GUI.DrawTexture(new Rect(x + i * 16, y, 10, 10), Texture2D.whiteTexture);
        }
        GUI.color = Color.white;
    }

    void DrawFloaters()
    {
        if (cam == null) return;
        GUIStyle st = Style(22, Color.white, TextAnchor.MiddleCenter);
        for (int i = 0; i < floaters.Count; i++)
        {
            Floater f = floaters[i];
            Vector3 sp = cam.WorldToScreenPoint(f.world);
            if (sp.z < 0f) continue;
            float guiY = Screen.height - sp.y;
            Color c = f.color;
            c.a = Mathf.Clamp01(f.life / 0.25f);
            st.normal.textColor = c;
            GUI.Label(new Rect(sp.x - 80, guiY - 16, 160, 32), f.text, st);
        }
    }

    void DrawSprite(Rect r, Sprite s)
    {
        if (s == null || s.texture == null) return;
        Rect tr = s.textureRect;
        Texture2D tex = s.texture;
        Rect coords = new Rect(tr.x / tex.width, tr.y / tex.height, tr.width / tex.width, tr.height / tex.height);
        GUI.DrawTextureWithTexCoords(r, tex, coords, true);
    }

    GUIStyle Style(int size, Color color, TextAnchor anchor)
    {
        GUIStyle s = new GUIStyle(GUI.skin.label);
        if (font != null) s.font = font;
        s.fontSize = size;
        s.alignment = anchor;
        s.fontStyle = FontStyle.Bold;
        s.normal.textColor = color;
        s.wordWrap = true;
        return s;
    }
}
