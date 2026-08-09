package com.imagetostl.android.gl

import android.opengl.GLES20
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import com.imagetostl.core.mesh.Mesh
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10

private const val VERTEX_SHADER = """
    uniform mat4 uMvpMatrix;
    uniform mat4 uRotationMatrix;
    attribute vec3 aPosition;
    attribute vec3 aNormal;
    varying vec3 vNormal;
    void main() {
        gl_Position = uMvpMatrix * vec4(aPosition, 1.0);
        vNormal = (uRotationMatrix * vec4(aNormal, 0.0)).xyz;
    }
"""

private const val FRAGMENT_SHADER = """
    precision mediump float;
    varying vec3 vNormal;
    void main() {
        vec3 lightDir = normalize(vec3(0.4, 0.6, 1.0));
        float diffuse = max(dot(normalize(vNormal), lightDir), 0.0);
        vec3 base = vec3(0.55, 0.62, 0.75);
        vec3 color = base * (0.35 + 0.65 * diffuse);
        gl_FragColor = vec4(color, 1.0);
    }
"""

/** Renders a [Mesh] as flat-shaded triangles with a fixed key light, rotated by touch drag. */
class MeshRenderer : GLSurfaceView.Renderer {

    @Volatile var rotationX = -25f
    @Volatile var rotationY = 0f

    private var program = 0
    private var positionHandle = 0
    private var normalHandle = 0
    private var mvpHandle = 0
    private var rotationHandle = 0

    private var vertexBuffer: FloatBuffer? = null
    private var normalBuffer: FloatBuffer? = null
    private var vertexCount = 0

    private var center = floatArrayOf(0f, 0f, 0f)
    private var radius = 100f

    private var viewportWidth = 1
    private var viewportHeight = 1

    fun setMesh(mesh: Mesh) {
        val positions = FloatArray(mesh.triangles.size * 9)
        val normals = FloatArray(mesh.triangles.size * 9)
        var i = 0
        for (t in mesh.triangles) {
            val n = t.normal()
            for (v in listOf(t.a, t.b, t.c)) {
                positions[i] = v.x.toFloat(); positions[i + 1] = v.y.toFloat(); positions[i + 2] = v.z.toFloat()
                normals[i] = n.x.toFloat(); normals[i + 1] = n.y.toFloat(); normals[i + 2] = n.z.toFloat()
                i += 3
            }
        }

        val (min, max) = mesh.bounds()
        center = floatArrayOf(
            ((min.x + max.x) / 2.0).toFloat(),
            ((min.y + max.y) / 2.0).toFloat(),
            ((min.z + max.z) / 2.0).toFloat(),
        )
        val extent = floatArrayOf((max.x - min.x).toFloat(), (max.y - min.y).toFloat(), (max.z - min.z).toFloat())
        radius = (maxOf(extent[0], extent[1], extent[2], 1f)) * 0.75f

        vertexBuffer = allocateFloatBuffer(positions)
        normalBuffer = allocateFloatBuffer(normals)
        vertexCount = mesh.triangles.size * 3
    }

    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        GLES20.glClearColor(0.086f, 0.094f, 0.106f, 1f)
        GLES20.glEnable(GLES20.GL_DEPTH_TEST)
        GLES20.glEnable(GLES20.GL_CULL_FACE)

        program = GLES20.glCreateProgram().also { p ->
            GLES20.glAttachShader(p, compileShader(GLES20.GL_VERTEX_SHADER, VERTEX_SHADER))
            GLES20.glAttachShader(p, compileShader(GLES20.GL_FRAGMENT_SHADER, FRAGMENT_SHADER))
            GLES20.glLinkProgram(p)
        }
        positionHandle = GLES20.glGetAttribLocation(program, "aPosition")
        normalHandle = GLES20.glGetAttribLocation(program, "aNormal")
        mvpHandle = GLES20.glGetUniformLocation(program, "uMvpMatrix")
        rotationHandle = GLES20.glGetUniformLocation(program, "uRotationMatrix")
    }

    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        viewportWidth = width.coerceAtLeast(1)
        viewportHeight = height.coerceAtLeast(1)
        GLES20.glViewport(0, 0, width, height)
    }

    override fun onDrawFrame(gl: GL10?) {
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT or GLES20.GL_DEPTH_BUFFER_BIT)
        val vBuf = vertexBuffer ?: return
        val nBuf = normalBuffer ?: return
        if (vertexCount == 0) return

        val rotation = FloatArray(16).also { Matrix.setIdentityM(it, 0) }
        Matrix.rotateM(rotation, 0, rotationX, 1f, 0f, 0f)
        Matrix.rotateM(rotation, 0, rotationY, 0f, 0f, 1f)

        val model = FloatArray(16)
        Matrix.setIdentityM(model, 0)
        Matrix.translateM(model, 0, -center[0], -center[1], -center[2])
        val rotatedModel = FloatArray(16)
        Matrix.multiplyMM(rotatedModel, 0, rotation, 0, model, 0)

        val view = FloatArray(16)
        val distance = radius * 3.2f
        Matrix.setLookAtM(view, 0, 0f, 0f, distance, 0f, 0f, 0f, 0f, 1f, 0f)

        val projection = FloatArray(16)
        val aspect = viewportWidth.toFloat() / viewportHeight.toFloat()
        Matrix.perspectiveM(projection, 0, 45f, aspect, radius * 0.05f, radius * 20f)

        val viewModel = FloatArray(16)
        Matrix.multiplyMM(viewModel, 0, view, 0, rotatedModel, 0)
        val mvp = FloatArray(16)
        Matrix.multiplyMM(mvp, 0, projection, 0, viewModel, 0)

        GLES20.glUseProgram(program)
        GLES20.glUniformMatrix4fv(mvpHandle, 1, false, mvp, 0)
        GLES20.glUniformMatrix4fv(rotationHandle, 1, false, rotation, 0)

        vBuf.position(0)
        GLES20.glEnableVertexAttribArray(positionHandle)
        GLES20.glVertexAttribPointer(positionHandle, 3, GLES20.GL_FLOAT, false, 0, vBuf)

        nBuf.position(0)
        GLES20.glEnableVertexAttribArray(normalHandle)
        GLES20.glVertexAttribPointer(normalHandle, 3, GLES20.GL_FLOAT, false, 0, nBuf)

        GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, vertexCount)

        GLES20.glDisableVertexAttribArray(positionHandle)
        GLES20.glDisableVertexAttribArray(normalHandle)
    }

    private fun compileShader(type: Int, source: String): Int =
        GLES20.glCreateShader(type).also { shader ->
            GLES20.glShaderSource(shader, source)
            GLES20.glCompileShader(shader)
        }

    private fun allocateFloatBuffer(data: FloatArray): FloatBuffer =
        ByteBuffer.allocateDirect(data.size * 4)
            .order(ByteOrder.nativeOrder())
            .asFloatBuffer()
            .apply { put(data); position(0) }
}
