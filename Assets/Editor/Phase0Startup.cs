#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// Opens the playable court once per editor session so Play is one click away.
[InitializeOnLoad]
public static class Phase0Startup
{
    const string ScenePath = "Assets/Scenes/Phase0_Court.unity";
    const string Flag = "HKPetVolleyball.OpenedCourt";

    static Phase0Startup()
    {
        EditorApplication.delayCall += OpenOnce;
    }

    static void OpenOnce()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return;
        if (EditorApplication.isCompiling || EditorApplication.isUpdating)
        {
            EditorApplication.delayCall += OpenOnce;
            return;
        }
        if (SessionState.GetBool(Flag, false)) return;
        if (!System.IO.File.Exists(ScenePath)) return;

        SessionState.SetBool(Flag, true);
        Scene active = EditorSceneManager.GetActiveScene();
        if (active.path == ScenePath) return;
        try
        {
            EditorSceneManager.OpenScene(ScenePath);
        }
        catch (System.Exception e)
        {
            Debug.LogWarning("HK Pet Volleyball could not auto-open the court scene. Open Assets/Scenes/Phase0_Court.unity yourself. " + e.Message);
        }
    }
}
#endif
