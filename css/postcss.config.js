/*
 * SPDX-FileCopyrightText: 2025 David Mandelberg <david@mandelberg.org>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

module.exports = {
  plugins: [
    // TODO: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=989704 - Use
    // postcss-preset-env too.
    require('postcss-preset-evergreen'),
  ],
}
