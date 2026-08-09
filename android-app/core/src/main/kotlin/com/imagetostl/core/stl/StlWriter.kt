package com.imagetostl.core.stl

import com.imagetostl.core.mesh.Mesh
import java.io.OutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

object StlWriter {

    /** Writes [mesh] as a binary STL (80-byte header, uint32 triangle count, then 50 bytes/triangle). */
    fun writeBinary(mesh: Mesh, out: OutputStream) {
        val header = ByteArray(80)
        out.write(header)

        val countBuf = ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN)
        countBuf.putInt(mesh.triangles.size)
        out.write(countBuf.array())

        val triBuf = ByteBuffer.allocate(50).order(ByteOrder.LITTLE_ENDIAN)
        for (t in mesh.triangles) {
            triBuf.clear()
            val n = t.normal()
            triBuf.putFloat(n.x.toFloat()); triBuf.putFloat(n.y.toFloat()); triBuf.putFloat(n.z.toFloat())
            for (v in listOf(t.a, t.b, t.c)) {
                triBuf.putFloat(v.x.toFloat()); triBuf.putFloat(v.y.toFloat()); triBuf.putFloat(v.z.toFloat())
            }
            triBuf.putShort(0) // attribute byte count
            out.write(triBuf.array())
        }
    }
}
