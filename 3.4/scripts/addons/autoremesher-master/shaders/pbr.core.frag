#version 330
/****************************************************************************
**
** Copyright (C) 2017 Klaralvdalens Datakonsult AB (KDAB).
** Contact: https://www.qt.io/licensing/
**
** This file is part of the Qt3D module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** BSD License Usage
** Alternatively, you may use this file under the terms of the BSD license
** as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
****************************************************************************/
/*
 *  Copyright (c) 2016-2020 Jeremy HU <jeremy-at-dust3d dot org>. All rights reserved. 
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy
 *  of this software and associated documentation files (the "Software"), to deal
 *  in the Software without restriction, including without limitation the rights
 *  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 *  copies of the Software, and to permit persons to whom the Software is
 *  furnished to do so, subject to the following conditions:

 *  The above copyright notice and this permission notice shall be included in all
 *  copies or substantial portions of the Software.

 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 *  SOFTWARE.
 */

// Please note that, this file "pbr.frag" is copied and slightly modified from the Qt3D's pbr shader "metalrough.inc.frag"
// https://github.com/qt/qt3d/blob/5.11/src/extras/shaders/gl3/metalrough.inc.frag

// Exposure correction
float exposure;
// Gamma correction
float gamma;

in vec3 vert;
in vec3 vertRaw;
in vec3 vertNormal;
in vec3 vertColor;
in vec2 vertTexCoord;
in float vertMetalness;
in float vertRoughness;
in vec3 cameraPos;
in vec3 firstLightPos;
in vec3 secondLightPos;
in vec3 thirdLightPos;
in float vertAlpha;
out vec4 fragColor;
uniform sampler2D textureId;
uniform int textureEnabled;
uniform sampler2D normalMapId;
uniform int normalMapEnabled;
uniform sampler2D metalnessRoughnessAmbientOcclusionMapId;
uniform int metalnessMapEnabled;
uniform int roughnessMapEnabled;
uniform int ambientOcclusionMapEnabled;
uniform int mousePickEnabled;
uniform vec3 mousePickTargetPosition;
uniform float mousePickRadius;
uniform samplerCube environmentIrradianceMapId;
uniform int environmentIrradianceMapEnabled;
uniform samplerCube environmentSpecularMapId;
uniform int environmentSpecularMapEnabled;

const int MAX_LIGHTS = 8;
const int TYPE_POINT = 0;
const int TYPE_DIRECTIONAL = 1;
const int TYPE_SPOT = 2;
struct Light {
    int type;
    vec3 position;
    vec3 color;
    float intensity;
    vec3 direction;
    float constantAttenuation;
    float linearAttenuation;
    float quadraticAttenuation;
    float cutOffAngle;
};
int lightCount;
Light lights[MAX_LIGHTS];

int mipLevelCount(const in samplerCube cube)
{
    int baseSize = textureSize(cube, 0).x;
    int nMips = int(log2(float(baseSize > 0 ? baseSize : 1))) + 1;
    return nMips;
}

float remapRoughness(const in float roughness)
{
    // As per page 14 of
    // http://www.frostbite.com/wp-content/uploads/2014/11/course_notes_moving_frostbite_to_pbr.pdf
    // we remap the roughness to give a more perceptually linear response
    // of "bluriness" as a function of the roughness specified by the user.
    // r = roughness^2
    float maxSpecPower;
    float minRoughness;
    maxSpecPower = 999999.0;
    minRoughness = sqrt(2.0 / (maxSpecPower + 2.0));
    return max(roughness * roughness, minRoughness);
}

float alphaToMipLevel(float alpha)
{
    float specPower = 2.0 / (alpha * alpha) - 2.0;

    // We use the mip level calculation from Lys' default power drop, which in
    // turn is a slight modification of that used in Marmoset Toolbag. See
    // https://docs.knaldtech.com/doku.php?id=specular_lys for details.
    // For now we assume a max specular power of 999999 which gives
    // maxGlossiness = 1.
    const float k0 = 0.00098;
    const float k1 = 0.9921;
    float glossiness = (pow(2.0, -10.0 / sqrt(specPower)) - k0) / k1;

    // TODO: Optimize by doing this on CPU and set as
    // uniform int environmentSpecularMapIdMipLevels say (if present in shader).
    // Lookup the number of mips in the specular envmap
    int mipLevels = mipLevelCount(environmentSpecularMapId);

    // Offset of smallest miplevel we should use (corresponds to specular
    // power of 1). I.e. in the 32x32 sized mip.
    const float mipOffset = 5.0;

    // The final factor is really 1 - g / g_max but as mentioned above g_max
    // is 1 by definition here so we can avoid the division. If we make the
    // max specular power for the spec map configurable, this will need to
    // be handled properly.
    float mipLevel = (mipLevels - 1.0 - mipOffset) * (1.0 - glossiness);
    return mipLevel;
}

float normalDistribution(const in vec3 n, const in vec3 h, const in float alpha)
{
    // Blinn-Phong approximation - see
    // http://graphicrants.blogspot.co.uk/2013/08/specular-brdf-reference.html
    float specPower = 2.0 / (alpha * alpha) - 2.0;
    return (specPower + 2.0) / (2.0 * 3.14159) * pow(max(dot(n, h), 0.0), specPower);
}

vec3 fresnelFactor(const in vec3 color, const in float cosineFactor)
{
    // Calculate the Fresnel effect value
    vec3 f = color;
    vec3 F = f + (1.0 - f) * pow(1.0 - cosineFactor, 5.0);
    return clamp(F, f, vec3(1.0));
}

float geometricModel(const in float lDotN,
                     const in float vDotN,
                     const in vec3 h)
{
    // Implicit geometric model (equal to denominator in specular model).
    // This currently assumes that there is no attenuation by geometric shadowing or
    // masking according to the microfacet theory.
    return lDotN * vDotN;
}

vec3 specularModel(const in vec3 F0,
                   const in float sDotH,
                   const in float sDotN,
                   const in float vDotN,
                   const in vec3 n,
                   const in vec3 h)
{
    // Clamp sDotN and vDotN to small positive value to prevent the
    // denominator in the reflection equation going to infinity. Balance this
    // by using the clamped values in the geometric factor function to
    // avoid ugly seams in the specular lighting.
    float sDotNPrime = max(sDotN, 0.001);
    float vDotNPrime = max(vDotN, 0.001);

    vec3 F = fresnelFactor(F0, sDotH);
    float G = geometricModel(sDotNPrime, vDotNPrime, h);

    vec3 cSpec = F * G / (4.0 * sDotNPrime * vDotNPrime);
    return clamp(cSpec, vec3(0.0), vec3(1.0));
}

vec3 pbrModel(const in int lightIndex,
              const in vec3 wPosition,
              const in vec3 wNormal,
              const in vec3 wView,
              const in vec3 baseColor,
              const in float metalness,
              const in float alpha,
              const in float ambientOcclusion)
{
    // Calculate some useful quantities
    vec3 n = wNormal;
    vec3 s = vec3(0.0);
    vec3 v = wView;
    vec3 h = vec3(0.0);

    float vDotN = dot(v, n);
    float sDotN = 0.0;
    float sDotH = 0.0;
    float att = 1.0;

    if (lights[lightIndex].type != TYPE_DIRECTIONAL) {
        // Point and Spot lights
        vec3 sUnnormalized = vec3(lights[lightIndex].position) - wPosition;
        s = normalize(sUnnormalized);

        // Calculate the attenuation factor
        sDotN = dot(s, n);
        if (sDotN > 0.0) {
            if (lights[lightIndex].constantAttenuation != 0.0
             || lights[lightIndex].linearAttenuation != 0.0
             || lights[lightIndex].quadraticAttenuation != 0.0) {
                float dist = length(sUnnormalized);
                att = 1.0 / (lights[lightIndex].constantAttenuation +
                             lights[lightIndex].linearAttenuation * dist +
                             lights[lightIndex].quadraticAttenuation * dist * dist);
            }

            // The light direction is in world space already
            if (lights[lightIndex].type == TYPE_SPOT) {
                // Check if fragment is inside or outside of the spot light cone
                if (degrees(acos(dot(-s, lights[lightIndex].direction))) > lights[lightIndex].cutOffAngle)
                    sDotN = 0.0;
            }
        }
    } else {
        // Directional lights
        // The light direction is in world space already
        s = normalize(-lights[lightIndex].direction);
        sDotN = dot(s, n);
    }

    h = normalize(s + v);
    sDotH = dot(s, h);

    // Calculate diffuse component
    vec3 diffuseColor = (1.0 - metalness) * baseColor * lights[lightIndex].color;
    vec3 diffuse = diffuseColor * max(sDotN, 0.0) / 3.14159;

    // Calculate specular component
    vec3 dielectricColor = vec3(0.04);
    vec3 F0 = mix(dielectricColor, baseColor, metalness);
    vec3 specularFactor = vec3(0.0);
    if (sDotN > 0.0) {
        specularFactor = specularModel(F0, sDotH, sDotN, vDotN, n, h);
        specularFactor *= normalDistribution(n, h, alpha);
    }
    vec3 specularColor = lights[lightIndex].color;
    vec3 specular = specularColor * specularFactor;

    // Blend between diffuse and specular to conserver energy
    vec3 color = att * lights[lightIndex].intensity * (specular + diffuse * (vec3(1.0) - specular));

    // Reduce by ambient occlusion amount
    color *= ambientOcclusion;

    return color;
}

vec3 pbrIblModel(const in vec3 wNormal,
                 const in vec3 wView,
                 const in vec3 baseColor,
                 const in float metalness,
                 const in float alpha,
                 const in float ambientOcclusion)
{
    // Calculate reflection direction of view vector about surface normal
    // vector in world space. This is used in the fragment shader to sample
    // from the environment textures for a light source. This is equivalent
    // to the l vector for punctual light sources. Armed with this, calculate
    // the usual factors needed
    vec3 n = wNormal;
    vec3 l = reflect(-wView, n);
    vec3 v = wView;
    vec3 h = normalize(l + v);
    float vDotN = dot(v, n);
    float lDotN = dot(l, n);
    float lDotH = dot(l, h);

    // Calculate diffuse component
    vec3 diffuseColor = (1.0 - metalness) * baseColor;
    vec3 diffuse = diffuseColor * texture(environmentIrradianceMapId, l).rgb;

    // Calculate specular component
    vec3 dielectricColor = vec3(0.04);
    vec3 F0 = mix(dielectricColor, baseColor, metalness);
    vec3 specularFactor = specularModel(F0, lDotH, lDotN, vDotN, n, h);

    float lod = alphaToMipLevel(alpha);
//#define DEBUG_SPECULAR_LODS
#ifdef DEBUG_SPECULAR_LODS
    if (lod > 7.0)
        return vec3(1.0, 0.0, 0.0);
    else if (lod > 6.0)
        return vec3(1.0, 0.333, 0.0);
    else if (lod > 5.0)
        return vec3(1.0, 1.0, 0.0);
    else if (lod > 4.0)
        return vec3(0.666, 1.0, 0.0);
    else if (lod > 3.0)
        return vec3(0.0, 1.0, 0.666);
    else if (lod > 2.0)
        return vec3(0.0, 0.666, 1.0);
    else if (lod > 1.0)
        return vec3(0.0, 0.0, 1.0);
    else if (lod > 0.0)
        return vec3(1.0, 0.0, 1.0);
#endif
    vec3 specularSkyColor = textureLod(environmentSpecularMapId, l, lod).rgb;
    vec3 specular = specularSkyColor * specularFactor;

    // Blend between diffuse and specular to conserve energy
    vec3 color = specular + diffuse * (vec3(1.0) - specularFactor);

    // Reduce by ambient occlusion amount
    color *= ambientOcclusion;

    return color;
}

vec3 toneMap(const in vec3 c)
{
    return c / (c + vec3(1.0));
}

vec3 gammaCorrect(const in vec3 color)
{
    return pow(color, vec3(1.0 / gamma));
}

// http://lolengine.net/blog/2013/07/27/rgb-to-hsv-in-glsl
vec3 rgb2hsv(vec3 c)
{
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c)
{
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec4 metalRoughFunction(const in vec4 baseColor,
                        const in float metalness,
                        const in float roughness,
                        const in float ambientOcclusion,
                        const in vec3 worldPosition,
                        const in vec3 worldView,
                        const in vec3 worldNormal)
{
    vec3 cLinear = vec3(0.0);

    // Remap roughness for a perceptually more linear correspondence
    float alpha = remapRoughness(roughness);
    
    if (environmentIrradianceMapEnabled == 1) {
        cLinear += pbrIblModel(worldNormal,
            worldView,
            baseColor.rgb,
            metalness,
            alpha,
            ambientOcclusion);
    }
    
    for (int i = 0; i < lightCount; ++i) {
        cLinear += pbrModel(i,
                            worldPosition,
                            worldNormal,
                            worldView,
                            baseColor.rgb,
                            metalness,
                            alpha,
                            ambientOcclusion);
    }

    // Apply exposure correction
    cLinear *= pow(2.0, exposure);

    // Apply simple (Reinhard) tonemap transform to get into LDR range [0, 1]
    vec3 cToneMapped = toneMap(cLinear);

    // Apply gamma correction prior to display
    vec3 cGamma = gammaCorrect(cToneMapped);

    return vec4(cGamma, baseColor.a);
}

void main() 
{
    // FIXME: don't hard code here
    exposure = 1.0;
    gamma = 2.2;

    // Light settings:
    // https://doc-snapshots.qt.io/qt5-5.12/qt3d-pbr-materials-lights-qml.html
    lightCount = 3;

    // Key light 
    lights[0].type = TYPE_POINT;
    lights[0].position = firstLightPos;
    lights[0].color = vec3(1.0, 1.0, 1.0);
    lights[0].intensity = 3.0;
    lights[0].constantAttenuation = 0.0;
    lights[0].linearAttenuation = 0.0;
    lights[0].quadraticAttenuation = 0.0;

    // Fill light
    lights[1].type = TYPE_POINT;
    lights[1].position = secondLightPos;
    lights[1].color = vec3(1.0, 1.0, 1.0);
    lights[1].intensity = 1.0;
    lights[1].constantAttenuation = 0.0;
    lights[1].linearAttenuation = 0.0;
    lights[1].quadraticAttenuation = 0.0;

    // Rim light
    lights[2].type = TYPE_POINT;
    lights[2].position = thirdLightPos;
    lights[2].color = vec3(1.0, 1.0, 1.0);
    lights[2].intensity = 0.5;
    lights[2].constantAttenuation = 0.0;
    lights[2].linearAttenuation = 0.0;
    lights[2].quadraticAttenuation = 0.0;

    vec3 color = vertColor;
    float alpha = vertAlpha;
    if (textureEnabled == 1) {
        vec4 textColor = texture(textureId, vertTexCoord);
        color = textColor.rgb;
        alpha = textColor.a;
    }
    if (mousePickEnabled == 1) {
        float distanceWithMouse = distance(mousePickTargetPosition, vertRaw);
        if (distanceWithMouse >= mousePickRadius * 0.94 && distanceWithMouse <= mousePickRadius) {
            color = color + vec3(0.99, 0.4, 0.13);
        }
    }
    color = pow(color, vec3(gamma));

    vec3 normal = vertNormal;
    if (normalMapEnabled == 1) {
        normal = texture(normalMapId, vertTexCoord).rgb;
        normal = normalize(normal * 2.0 - 1.0);
    }

    // Red: Ambient Occlusion
    // Green: Roughness
    // Blue: Metallic

    float metalness = vertMetalness;
    if (metalnessMapEnabled == 1) {
        metalness = texture(metalnessRoughnessAmbientOcclusionMapId, vertTexCoord).b;
    }

    float roughness = vertRoughness;
    if (roughnessMapEnabled == 1) {
        roughness = texture(metalnessRoughnessAmbientOcclusionMapId, vertTexCoord).g;
    }

    float ambientOcclusion = 1.0;
    if (ambientOcclusionMapEnabled == 1) {
        ambientOcclusion = texture(metalnessRoughnessAmbientOcclusionMapId, vertTexCoord).r;
    }
    
    if (environmentIrradianceMapEnabled != 1) {
        roughness = min(0.99, roughness);
        metalness = min(0.99, metalness);
    }
    
    fragColor = metalRoughFunction(vec4(color, alpha),
                                      metalness,
                                      roughness,
                                      ambientOcclusion,
                                      vert,
                                      normalize(cameraPos - vert),
                                      normal);
}
