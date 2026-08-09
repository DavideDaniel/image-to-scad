package com.imagetostl.android.gl

import android.content.Context
import android.opengl.GLSurfaceView
import android.view.MotionEvent
import com.imagetostl.core.mesh.Mesh

class MeshGLSurfaceView(context: Context) : GLSurfaceView(context) {

    private val meshRenderer = MeshRenderer()
    private var lastX = 0f
    private var lastY = 0f

    init {
        setEGLContextClientVersion(2)
        setRenderer(meshRenderer)
        renderMode = RENDERMODE_WHEN_DIRTY
    }

    fun setMesh(mesh: Mesh) {
        queueEvent {
            meshRenderer.setMesh(mesh)
            requestRender()
        }
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                lastX = event.x
                lastY = event.y
            }
            MotionEvent.ACTION_MOVE -> {
                val dx = event.x - lastX
                val dy = event.y - lastY
                lastX = event.x
                lastY = event.y
                meshRenderer.rotationY += dx * 0.5f
                meshRenderer.rotationX = (meshRenderer.rotationX + dy * 0.5f).coerceIn(-89f, 89f)
                requestRender()
            }
        }
        return true
    }
}
