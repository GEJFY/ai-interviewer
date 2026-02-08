/**
 * Settings screen.
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useState } from 'react';

interface SettingItemProps {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle?: string;
  onPress?: () => void;
  rightElement?: React.ReactNode;
}

function SettingItem({ icon, title, subtitle, onPress, rightElement }: SettingItemProps) {
  return (
    <TouchableOpacity style={styles.settingItem} onPress={onPress} disabled={!onPress}>
      <View style={styles.settingIcon}>
        <Ionicons name={icon} size={22} color="#6b7280" />
      </View>
      <View style={styles.settingContent}>
        <Text style={styles.settingTitle}>{title}</Text>
        {subtitle && <Text style={styles.settingSubtitle}>{subtitle}</Text>}
      </View>
      {rightElement || (onPress && (
        <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
      ))}
    </TouchableOpacity>
  );
}

export default function SettingsScreen() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [autoTranscribe, setAutoTranscribe] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  return (
    <ScrollView style={styles.container}>
      {/* Profile Section */}
      <View style={styles.profileSection}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>GY</Text>
        </View>
        <View style={styles.profileInfo}>
          <Text style={styles.profileName}>Goyos User</Text>
          <Text style={styles.profileEmail}>user@example.com</Text>
        </View>
        <TouchableOpacity>
          <Ionicons name="pencil" size={20} color="#2563eb" />
        </TouchableOpacity>
      </View>

      {/* General Settings */}
      <Text style={styles.sectionTitle}>一般設定</Text>
      <View style={styles.section}>
        <SettingItem
          icon="language"
          title="言語"
          subtitle="日本語"
          onPress={() => {}}
        />
        <SettingItem
          icon="moon"
          title="ダークモード"
          rightElement={
            <Switch
              value={darkMode}
              onValueChange={setDarkMode}
              trackColor={{ false: '#d1d5db', true: '#93c5fd' }}
              thumbColor={darkMode ? '#2563eb' : '#f4f4f5'}
            />
          }
        />
        <SettingItem
          icon="notifications"
          title="通知"
          rightElement={
            <Switch
              value={notificationsEnabled}
              onValueChange={setNotificationsEnabled}
              trackColor={{ false: '#d1d5db', true: '#93c5fd' }}
              thumbColor={notificationsEnabled ? '#2563eb' : '#f4f4f5'}
            />
          }
        />
      </View>

      {/* Interview Settings */}
      <Text style={styles.sectionTitle}>インタビュー設定</Text>
      <View style={styles.section}>
        <SettingItem
          icon="mic"
          title="自動文字起こし"
          subtitle="音声を自動でテキストに変換"
          rightElement={
            <Switch
              value={autoTranscribe}
              onValueChange={setAutoTranscribe}
              trackColor={{ false: '#d1d5db', true: '#93c5fd' }}
              thumbColor={autoTranscribe ? '#2563eb' : '#f4f4f5'}
            />
          }
        />
        <SettingItem
          icon="volume-high"
          title="AI音声応答"
          subtitle="有効"
          onPress={() => {}}
        />
        <SettingItem
          icon="globe"
          title="翻訳言語"
          subtitle="日本語 ↔ 英語"
          onPress={() => {}}
        />
      </View>

      {/* Account Settings */}
      <Text style={styles.sectionTitle}>アカウント</Text>
      <View style={styles.section}>
        <SettingItem
          icon="key"
          title="パスワード変更"
          onPress={() => {}}
        />
        <SettingItem
          icon="shield-checkmark"
          title="二要素認証"
          subtitle="無効"
          onPress={() => {}}
        />
        <SettingItem
          icon="cloud-download"
          title="データエクスポート"
          onPress={() => {}}
        />
      </View>

      {/* Support */}
      <Text style={styles.sectionTitle}>サポート</Text>
      <View style={styles.section}>
        <SettingItem
          icon="help-circle"
          title="ヘルプ"
          onPress={() => {}}
        />
        <SettingItem
          icon="chatbubble-ellipses"
          title="お問い合わせ"
          onPress={() => {}}
        />
        <SettingItem
          icon="information-circle"
          title="アプリについて"
          subtitle="バージョン 1.0.0"
          onPress={() => {}}
        />
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutButton}>
        <Ionicons name="log-out" size={20} color="#ef4444" />
        <Text style={styles.logoutText}>ログアウト</Text>
      </TouchableOpacity>

      <View style={styles.footer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  profileSection: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 20,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#2563eb',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
  },
  profileInfo: {
    flex: 1,
    marginLeft: 16,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  profileEmail: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6b7280',
    paddingHorizontal: 20,
    paddingBottom: 8,
    textTransform: 'uppercase',
  },
  section: {
    backgroundColor: '#fff',
    marginBottom: 20,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  settingIcon: {
    width: 36,
  },
  settingContent: {
    flex: 1,
  },
  settingTitle: {
    fontSize: 15,
    color: '#1f2937',
  },
  settingSubtitle: {
    fontSize: 13,
    color: '#9ca3af',
    marginTop: 2,
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fff',
    padding: 16,
    marginHorizontal: 20,
    borderRadius: 12,
    marginBottom: 20,
  },
  logoutText: {
    color: '#ef4444',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  footer: {
    height: 40,
  },
});
