/**
 * Home screen - Dashboard for the mobile app.
 */

import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Ionicons name={icon} size={24} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statTitle}>{title}</Text>
    </View>
  );
}

interface QuickActionProps {
  title: string;
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
}

function QuickAction({ title, icon, onPress }: QuickActionProps) {
  return (
    <TouchableOpacity style={styles.quickAction} onPress={onPress}>
      <Ionicons name={icon} size={28} color="#2563eb" />
      <Text style={styles.quickActionText}>{title}</Text>
    </TouchableOpacity>
  );
}

export default function HomeScreen() {
  const router = useRouter();

  // Mock data - would fetch from API
  const stats = {
    activeProjects: 3,
    pendingTasks: 5,
    todayInterviews: 2,
    completedThisWeek: 8,
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.greeting}>おはようございます</Text>
        <Text style={styles.date}>
          {new Date().toLocaleDateString('ja-JP', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </Text>
      </View>

      {/* Stats Grid */}
      <View style={styles.statsGrid}>
        <StatCard
          title="進行中案件"
          value={stats.activeProjects}
          icon="folder-open"
          color="#2563eb"
        />
        <StatCard
          title="未完了タスク"
          value={stats.pendingTasks}
          icon="checkbox-outline"
          color="#f59e0b"
        />
        <StatCard
          title="本日の予定"
          value={stats.todayInterviews}
          icon="calendar"
          color="#10b981"
        />
        <StatCard
          title="今週完了"
          value={stats.completedThisWeek}
          icon="checkmark-circle"
          color="#8b5cf6"
        />
      </View>

      {/* Quick Actions */}
      <Text style={styles.sectionTitle}>クイックアクション</Text>
      <View style={styles.quickActions}>
        <QuickAction
          title="新規インタビュー"
          icon="add-circle"
          onPress={() => router.push('/interviews')}
        />
        <QuickAction
          title="タスク確認"
          icon="list"
          onPress={() => router.push('/tasks')}
        />
        <QuickAction
          title="レポート作成"
          icon="document-text"
          onPress={() => {}}
        />
        <QuickAction
          title="ナレッジ検索"
          icon="search"
          onPress={() => {}}
        />
      </View>

      {/* Recent Activity */}
      <Text style={styles.sectionTitle}>最近のアクティビティ</Text>
      <View style={styles.activityList}>
        <View style={styles.activityItem}>
          <Ionicons name="chatbubbles" size={20} color="#6b7280" />
          <View style={styles.activityContent}>
            <Text style={styles.activityText}>
              経理部インタビュー完了
            </Text>
            <Text style={styles.activityTime}>2時間前</Text>
          </View>
        </View>
        <View style={styles.activityItem}>
          <Ionicons name="document" size={20} color="#6b7280" />
          <View style={styles.activityContent}>
            <Text style={styles.activityText}>
              業務記述書を生成
            </Text>
            <Text style={styles.activityTime}>5時間前</Text>
          </View>
        </View>
        <View style={styles.activityItem}>
          <Ionicons name="checkmark-circle" size={20} color="#10b981" />
          <View style={styles.activityContent}>
            <Text style={styles.activityText}>
              RCMレビュー完了
            </Text>
            <Text style={styles.activityTime}>昨日</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  header: {
    padding: 20,
    backgroundColor: '#2563eb',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  date: {
    fontSize: 14,
    color: '#bfdbfe',
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
  },
  statCard: {
    width: '46%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    margin: '2%',
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
    marginTop: 8,
  },
  statTitle: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 10,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 10,
  },
  quickAction: {
    width: '23%',
    aspectRatio: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    margin: '1%',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  quickActionText: {
    fontSize: 10,
    color: '#4b5563',
    marginTop: 6,
    textAlign: 'center',
  },
  activityList: {
    backgroundColor: '#fff',
    marginHorizontal: 14,
    borderRadius: 12,
    marginBottom: 20,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  activityContent: {
    marginLeft: 12,
    flex: 1,
  },
  activityText: {
    fontSize: 14,
    color: '#1f2937',
  },
  activityTime: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
  },
});
